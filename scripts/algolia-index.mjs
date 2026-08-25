/**
 * Crawl the published Docusaurus site and replace the Algolia DocSearch index.
 *
 * Required:
 *   ALGOLIA_ADMIN_API_KEY   Admin or Write key (addObject / deleteObject / settings)
 *
 * Optional:
 *   ALGOLIA_APP_ID
 *   ALGOLIA_INDEX_NAME
 *   ALGOLIA_SITE_URL
 *   ALGOLIA_SEARCH_API_KEY  used only for the post-upload smoke query
 *
 * Usage:
 *   npm run algolia:index
 *   node scripts/algolia-index.mjs --dry-run
 */
import "dotenv/config";
import { createHash } from "node:crypto";
import { load } from "cheerio";

const APP_ID = process.env.ALGOLIA_APP_ID || "1VU781LYTV";
const INDEX_NAME = process.env.ALGOLIA_INDEX_NAME || "case_doc";
const SITE_URL = ensureTrailingSlash(
  process.env.ALGOLIA_SITE_URL || "https://developer.d-robotics.cc/case_doc/",
);
const SEARCH_API_KEY =
  process.env.ALGOLIA_SEARCH_API_KEY || "fb65c6e54a52ce6fba0645bd2630e79b";
const ADMIN_API_KEY = process.env.ALGOLIA_ADMIN_API_KEY;
const DRY_RUN = process.argv.includes("--dry-run");
const USER_AGENT =
  "case-doc-algolia-indexer/1.0 (+https://developer.d-robotics.cc/case_doc/)";

const SKIP_PATH =
  /\/search\/?$|\.(?:png|jpe?g|gif|svg|webp|ico|pdf|zip|mp4|css|js|map|xml|txt|json)$/i;
const LEVEL_WEIGHT = {
  lvl0: 100,
  lvl1: 90,
  lvl2: 80,
  lvl3: 70,
  lvl4: 60,
  lvl5: 50,
  lvl6: 40,
  content: 0,
};
const INDEX_SETTINGS = {
  searchableAttributes: [
    "unordered(hierarchy.lvl0)",
    "unordered(hierarchy.lvl1)",
    "unordered(hierarchy.lvl2)",
    "unordered(hierarchy.lvl3)",
    "unordered(hierarchy.lvl4)",
    "unordered(hierarchy.lvl5)",
    "unordered(hierarchy.lvl6)",
    "content",
  ],
  attributesToRetrieve: [
    "hierarchy",
    "content",
    "anchor",
    "url",
    "url_without_anchor",
    "type",
    "lang",
    "language",
    "version",
    "docusaurus_tag",
  ],
  attributesToHighlight: ["hierarchy", "content"],
  attributesToSnippet: ["content:10"],
  camelCaseAttributes: ["hierarchy", "content"],
  attributesForFaceting: [
    "type",
    "lang",
    "language",
    "version",
    "docusaurus_tag",
  ],
  distinct: true,
  attributeForDistinct: "url",
  customRanking: [
    "desc(weight.pageRank)",
    "desc(weight.level)",
    "asc(weight.position)",
  ],
  ranking: [
    "words",
    "filters",
    "typo",
    "attribute",
    "proximity",
    "exact",
    "custom",
  ],
  highlightPreTag: '<span class="algolia-docsearch-suggestion--highlight">',
  highlightPostTag: "</span>",
  minWordSizefor1Typo: 3,
  minWordSizefor2Typos: 7,
  allowTyposOnNumericTokens: false,
  minProximity: 1,
  ignorePlurals: true,
  advancedSyntax: true,
  attributeCriteriaComputedByMinProximity: true,
  removeWordsIfNoResults: "allOptional",
  separatorsToIndex: "_",
};

function ensureTrailingSlash(url) {
  return url.endsWith("/") ? url : `${url}/`;
}

function normalizePageUrl(raw, base) {
  let url;
  try {
    url = new URL(raw, base);
  } catch {
    return null;
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    return null;
  }
  const site = new URL(SITE_URL);
  if (url.origin !== site.origin) {
    return null;
  }
  if (!url.pathname.startsWith(site.pathname.replace(/\/$/, "") + "/") &&
      url.pathname !== site.pathname.replace(/\/$/, "") &&
      url.pathname !== site.pathname) {
    return null;
  }
  url.hash = "";
  url.search = "";
  url.pathname = url.pathname.replace(/\/index\.html$/i, "/");
  if (url.pathname.length > 1) {
    url.pathname = url.pathname.replace(/\/+$/, "");
  }
  if (SKIP_PATH.test(url.pathname)) {
    return null;
  }
  return url.toString();
}

function meta($, name) {
  return (
    $(`meta[name="${name}"]`).attr("content") ||
    $(`meta[name="${name.toLowerCase()}"]`).attr("content") ||
    ""
  ).trim();
}

function visibleText($el) {
  const clone = $el.clone();
  clone.find("script, style, .hash-link, svg, button, noscript").remove();
  return clone.text().replace(/\s+/g, " ").trim();
}

function headingAnchor($el) {
  return ($el.attr("id") || $el.find("[id]").first().attr("id") || "").trim();
}

function emptyHierarchy() {
  return {
    lvl0: null,
    lvl1: null,
    lvl2: null,
    lvl3: null,
    lvl4: null,
    lvl5: null,
    lvl6: null,
  };
}

function objectID(parts) {
  return createHash("sha1").update(parts.join("|")).digest("hex");
}

function splitContent(text, max = 7500) {
  if (text.length <= max) {
    return [text];
  }
  const chunks = [];
  let rest = text;
  while (rest.length > max) {
    let cut = rest.lastIndexOf(" ", max);
    if (cut < max / 2) {
      cut = max;
    }
    chunks.push(rest.slice(0, cut).trim());
    rest = rest.slice(cut).trim();
  }
  if (rest) {
    chunks.push(rest);
  }
  return chunks;
}

function extractRecords(pageUrl, html) {
  const $ = load(html);
  const canonical =
    normalizePageUrl($('link[rel="canonical"]').attr("href") || pageUrl, pageUrl) ||
    pageUrl;
  const language =
    meta($, "docsearch:language") ||
    $("html").attr("lang") ||
    "zh-Hans";
  const version = meta($, "docsearch:version") || "current";
  const docusaurusTag =
    meta($, "docsearch:docusaurus_tag") ||
    meta($, "docusaurus_tag") ||
    "docs-default-current";

  const $article = $("article").first();
  if ($article.length === 0) {
    return [];
  }

  $article.find(".hash-link, .theme-doc-toc-mobile, script, style").remove();

  const navbarTitle = $(".navbar__item.navbar__link--active").first().text().trim();
  const crumbs = $(".breadcrumbs__link")
    .toArray()
    .map((el) => visibleText($(el)))
    .filter(Boolean);
  const lvl0 =
    [navbarTitle, ...crumbs].filter(Boolean).join(" / ") || "Documentation";

  const $root = $article.find(".theme-doc-markdown").length
    ? $article.find(".theme-doc-markdown").first()
    : $article;

  const hierarchy = emptyHierarchy();
  hierarchy.lvl0 = lvl0;
  let currentAnchor = "";
  let position = 0;
  let contentBuffer = [];
  const records = [];

  const flushContent = () => {
    const text = contentBuffer.join(" ").replace(/\s+/g, " ").trim();
    contentBuffer = [];
    if (!text) {
      return;
    }
    for (const chunk of splitContent(text)) {
      position += 1;
      const url = currentAnchor ? `${canonical}#${currentAnchor}` : canonical;
      records.push({
        objectID: objectID([url, "content", String(position), chunk]),
        hierarchy: { ...hierarchy },
        content: chunk,
        type: "content",
        url,
        url_without_anchor: canonical,
        anchor: currentAnchor || null,
        language,
        lang: language,
        version,
        docusaurus_tag: docusaurusTag,
        weight: {
          pageRank: 0,
          level: LEVEL_WEIGHT.content,
          position,
        },
      });
    }
  };

  const nodes = $root
    .find(
      "h1, h2, h3, h4, h5, h6, p, li, td:first-child, td:last-child",
    )
    .toArray();

  for (const node of nodes) {
    const $el = $(node);
    const tag = (node.tagName || node.name || "").toLowerCase();
    if (!tag) {
      continue;
    }

    if (/^h[1-6]$/.test(tag)) {
      flushContent();
      const level = Number(tag.slice(1));
      const text = visibleText($el);
      if (!text) {
        continue;
      }
      for (let i = level; i <= 6; i += 1) {
        hierarchy[`lvl${i}`] = null;
      }
      hierarchy[`lvl${level}`] = text;
      currentAnchor = headingAnchor($el);
      position += 1;
      const type = `lvl${level}`;
      const url = currentAnchor ? `${canonical}#${currentAnchor}` : canonical;
      records.push({
        objectID: objectID([url, type, String(position), text]),
        hierarchy: { ...hierarchy },
        content: null,
        type,
        url,
        url_without_anchor: canonical,
        anchor: currentAnchor || null,
        language,
        lang: language,
        version,
        docusaurus_tag: docusaurusTag,
        weight: {
          pageRank: 0,
          level: LEVEL_WEIGHT[type],
          position,
        },
      });
      continue;
    }

    if (tag === "td") {
      const $cells = $el.parent().children("td");
      const isFirst = $el.is($cells.first());
      const isLast = $el.is($cells.last());
      const text = visibleText($el);
      if (!text) {
        continue;
      }
      if (isFirst && $cells.length > 1) {
        flushContent();
        hierarchy.lvl5 = text;
        hierarchy.lvl6 = null;
        currentAnchor = headingAnchor($el) || currentAnchor;
        position += 1;
        const url = currentAnchor ? `${canonical}#${currentAnchor}` : canonical;
        records.push({
          objectID: objectID([url, "lvl5", String(position), text]),
          hierarchy: { ...hierarchy },
          content: null,
          type: "lvl5",
          url,
          url_without_anchor: canonical,
          anchor: currentAnchor || null,
          language,
          lang: language,
          version,
          docusaurus_tag: docusaurusTag,
          weight: {
            pageRank: 0,
            level: LEVEL_WEIGHT.lvl5,
            position,
          },
        });
        continue;
      }
      if (isLast) {
        contentBuffer.push(text);
      }
      continue;
    }

    if ($el.parents("li").length && tag === "p") {
      continue;
    }
    if (tag === "li" && $el.parents("li").length) {
      continue;
    }
    const text = visibleText($el);
    if (text) {
      contentBuffer.push(text);
    }
  }

  flushContent();

  if (records.length === 0 && hierarchy.lvl0) {
    const title = visibleText($("h1").first()) || $("title").first().text().trim();
    if (title) {
      hierarchy.lvl1 = title;
      records.push({
        objectID: objectID([canonical, "lvl1", title]),
        hierarchy: { ...hierarchy },
        content: null,
        type: "lvl1",
        url: canonical,
        url_without_anchor: canonical,
        anchor: null,
        language,
        lang: language,
        version,
        docusaurus_tag: docusaurusTag,
        weight: {
          pageRank: 0,
          level: LEVEL_WEIGHT.lvl1,
          position: 1,
        },
      });
    }
  }

  return records;
}

function extractLinks(pageUrl, html) {
  const $ = load(html);
  const urls = new Set();
  $("a[href]").each((_, el) => {
    const href = $(el).attr("href");
    const next = normalizePageUrl(href, pageUrl);
    if (next) {
      urls.add(next);
    }
  });
  return [...urls];
}

async function fetchHtml(url) {
  const candidates = [url];
  if (!url.endsWith("/")) {
    candidates.push(`${url}/`);
  }
  for (const candidate of candidates) {
    try {
      const res = await fetch(candidate, {
        headers: { "user-agent": USER_AGENT, accept: "text/html" },
        redirect: "follow",
      });
      const contentType = res.headers.get("content-type") || "";
      if (!res.ok || !contentType.includes("html")) {
        continue;
      }
      const html = await res.text();
      if (!html.includes("<html")) {
        continue;
      }
      const finalUrl =
        normalizePageUrl(res.url || candidate, candidate) || candidate;
      return { url: finalUrl, html };
    } catch (err) {
      console.warn(`Fetch failed ${candidate}: ${err.message}`);
    }
  }
  return null;
}

async function mapLimit(items, limit, worker) {
  const results = [];
  let index = 0;
  async function run() {
    while (index < items.length) {
      const current = index;
      index += 1;
      results[current] = await worker(items[current], current);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, run));
  return results;
}

async function crawl() {
  const site = new URL(SITE_URL);
  const startUrls = [
    SITE_URL,
    new URL("case", SITE_URL).href,
    new URL("en/", SITE_URL).href,
    new URL("en/case", SITE_URL).href,
  ]
    .map((url) => normalizePageUrl(url, SITE_URL))
    .filter(Boolean);

  const queue = [...new Set(startUrls)];
  const seen = new Set();
  const pages = [];

  while (queue.length) {
    const batch = [];
    while (queue.length && batch.length < 6) {
      const url = queue.shift();
      if (!seen.has(url)) {
        seen.add(url);
        batch.push(url);
      }
    }
    const fetched = await mapLimit(batch, 6, fetchHtml);
    for (const page of fetched) {
      if (!page) {
        continue;
      }
      pages.push(page);
      for (const link of extractLinks(page.url, page.html)) {
        if (!seen.has(link) && !queue.includes(link)) {
          queue.push(link);
        }
      }
    }
  }

  console.log(
    `Crawled ${pages.length} HTML pages under ${site.origin}${site.pathname}`,
  );
  return pages;
}

function algoliaHost(kind = "write") {
  return kind === "search"
    ? `https://${APP_ID}-dsn.algolia.net`
    : `https://${APP_ID}.algolia.net`;
}

async function algoliaRequest(path, { method = "GET", body, key, host } = {}) {
  const url = `${host || algoliaHost("write")}${path}`;
  const payload = body === undefined ? undefined : JSON.stringify(body);
  const res = await fetch(url, {
    method,
    headers: {
      "x-algolia-application-id": APP_ID,
      "x-algolia-api-key": key,
      "content-type": "application/json",
    },
    body: payload,
  });
  const text = await res.text();
  let json;
  try {
    json = text ? JSON.parse(text) : {};
  } catch {
    json = { message: text };
  }
  if (!res.ok) {
    const err = new Error(
      `Algolia ${method} ${path} → ${res.status}: ${json.message || text}`,
    );
    err.status = res.status;
    err.body = json;
    throw err;
  }
  return json;
}

function normalizeTaskIds(taskID) {
  if (taskID == null) {
    return [];
  }
  if (typeof taskID === "object") {
    return Object.values(taskID).filter((id) => id != null);
  }
  return [taskID];
}

async function waitTask(taskID) {
  for (const id of normalizeTaskIds(taskID)) {
    for (let i = 0; i < 60; i += 1) {
      const result = await algoliaRequest(
        `/1/indexes/${encodeURIComponent(INDEX_NAME)}/task/${id}`,
        { key: ADMIN_API_KEY },
      );
      if (result.status === "published") {
        break;
      }
      if (i === 59) {
        throw new Error(`Timed out waiting for Algolia task ${id}`);
      }
      await new Promise((resolve) => setTimeout(resolve, 400));
    }
  }
}

async function applySettings() {
  const result = await algoliaRequest(
    `/1/indexes/${encodeURIComponent(INDEX_NAME)}/settings`,
    { method: "PUT", body: INDEX_SETTINGS, key: ADMIN_API_KEY },
  );
  await waitTask(result.taskID);
  console.log(`Index settings applied: ${INDEX_NAME}`);
}

async function clearIndex() {
  const result = await algoliaRequest(
    `/1/indexes/${encodeURIComponent(INDEX_NAME)}/clear`,
    { method: "POST", key: ADMIN_API_KEY },
  );
  await waitTask(result.taskID);
  console.log(`Index cleared: ${INDEX_NAME}`);
}

async function uploadRecords(records) {
  const chunkSize = 500;
  for (let i = 0; i < records.length; i += chunkSize) {
    const chunk = records.slice(i, i + chunkSize);
    const result = await algoliaRequest(
      `/1/indexes/${encodeURIComponent(INDEX_NAME)}/batch`,
      {
        method: "POST",
        key: ADMIN_API_KEY,
        body: {
          requests: chunk.map((record) => ({
            action: "addObject",
            body: record,
          })),
        },
      },
    );
    await waitTask(result.taskID);
    console.log(
      `Uploaded ${Math.min(i + chunkSize, records.length)}/${records.length} records`,
    );
  }
}

async function smokeQuery() {
  const queries = [
    {
      label: "VLA / zh-Hans / docs-default-current",
      body: {
        query: "VLA",
        hitsPerPage: 3,
        facetFilters: ["language:zh-Hans", "docusaurus_tag:docs-default-current"],
      },
    },
    {
      label: "USB / en / docs-default-current",
      body: {
        query: "USB",
        hitsPerPage: 3,
        facetFilters: ["language:en", "docusaurus_tag:docs-default-current"],
      },
    },
  ];
  for (const item of queries) {
    const result = await algoliaRequest(
      `/1/indexes/${encodeURIComponent(INDEX_NAME)}/query`,
      {
        method: "POST",
        key: SEARCH_API_KEY,
        host: algoliaHost("search"),
        body: item.body,
      },
    );
    console.log(
      `Query "${item.label}": ${result.nbHits} hits` +
        (result.hits?.[0]?.url ? `; first=${result.hits[0].url}` : ""),
    );
  }
}

async function main() {
  if (!ADMIN_API_KEY) {
    console.error(
      "Missing ALGOLIA_ADMIN_API_KEY. Copy .env.example to .env and set the Admin/Write key.",
    );
    process.exit(1);
  }

  console.log(`Site: ${SITE_URL}`);
  console.log(`Index: ${APP_ID}/${INDEX_NAME}${DRY_RUN ? " (dry-run)" : ""}`);

  const pages = await crawl();
  const records = pages.flatMap((page) => extractRecords(page.url, page.html));
  const languages = [...new Set(records.map((r) => r.language))];
  const tags = [...new Set(records.map((r) => r.docusaurus_tag))];
  console.log(
    `Built ${records.length} records from ${pages.length} pages; languages=${languages.join(",") || "-"} tags=${tags.join(",") || "-"}`,
  );

  if (records.length === 0) {
    console.error("No records extracted. Aborting so the live index is not wiped.");
    process.exit(1);
  }

  if (DRY_RUN) {
    const sample = records[0];
    console.log("Dry-run sample record:", JSON.stringify(sample, null, 2));
    return;
  }

  await applySettings();
  await clearIndex();
  await uploadRecords(records);
  await smokeQuery();
  console.log("Algolia index update finished.");
}

main().catch((err) => {
  console.error(err);
  if (err.status === 403) {
    console.error(
      "Algolia returned 403. Unset HTTP(S)_PROXY if a local proxy is intercepting, and confirm the key has addObject/deleteObject/settings ACL.",
    );
  }
  process.exit(1);
});
