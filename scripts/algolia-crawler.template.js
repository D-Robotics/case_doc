/**
 * Algolia Crawler 配置模板（Docusaurus v2/v3）。
 * 粘贴到 Dashboard → Data sources → Crawler → Editor。
 * 不要把 Admin / Write API Key 写进仓库。
 */
new Crawler({
  appId: "YOUR_APP_ID",
  apiKey: "YOUR_CRAWLER_API_KEY",
  rateLimit: 8,
  maxDepth: 10,
  startUrls: [
    "https://developer.d-robotics.cc/case_doc/",
    "https://developer.d-robotics.cc/case_doc/case",
    "https://developer.d-robotics.cc/case_doc/en/case",
  ],
  sitemaps: ["https://developer.d-robotics.cc/case_doc/sitemap.xml"],
  ignoreCanonicalTo: true,
  discoveryPatterns: ["https://developer.d-robotics.cc/case_doc/**"],
  actions: [
    {
      indexName: "case_doc",
      pathsToMatch: ["https://developer.d-robotics.cc/case_doc/**"],
      recordExtractor: ({ $, helpers }) => {
        const navbarTitle = $(".navbar__item.navbar__link--active").text();
        const pageBreadcrumbTitles = $(".breadcrumbs__link")
          .toArray()
          .map((item) => $(item).text().trim())
          .filter(Boolean);
        const lvl0 =
          [navbarTitle, ...pageBreadcrumbTitles].join(" / ") || "Documentation";
        return helpers.docsearch({
          recordProps: {
            lvl0: {
              selectors: "",
              defaultValue: lvl0,
            },
            lvl1: ["header h1", "article h1"],
            lvl2: "article h2",
            lvl3: "article h3",
            lvl4: "article h4",
            lvl5: "article h5, article td:first-child",
            lvl6: "article h6",
            content: "article p, article li, article td:last-child",
          },
          indexHeadings: true,
          aggregateContent: true,
          recordVersion: "v3",
        });
      },
    },
  ],
  initialIndexSettings: {
    case_doc: {
      attributesForFaceting: [
        "type",
        "lang",
        "language",
        "version",
        "docusaurus_tag",
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
    },
  },
});
