/**
 * APEX Site Header Component (static-site friendly)
 * - Injects a shared <header id="header"> into a placeholder element: #site-header
 * - Sets active nav item based on current page/hash
 * - Designed to run immediately during parsing (place script right after placeholder)
 */
(function () {
  "use strict";

  var mount = document.getElementById("site-header");
  if (!mount) return;

  var path = (window.location.pathname || "").split("/").pop();
  if (!path) path = "index.html";

  var isIndex = path === "index.html";

  // Determine active item
  var hash = window.location.hash || "";
  var activeKey = "team";
  if (isIndex) {
    if (!hash || hash === "#hero") activeKey = "home";
    else if (hash === "#about") activeKey = "about";
    else activeKey = "home";
  } else if (path === "publications.html") activeKey = "publications";
  else if (path === "portfolio.html" || path === "portfolio-details.html") activeKey = "portfolio";
  else if (path === "misc.html") activeKey = "misc";
  else if (path === "news.html") activeKey = "news"; // not shown in top nav currently
  else if (path === "team.html") activeKey = "team";

  var headerClass = isIndex
    ? "header d-flex align-items-center fixed-top"
    : "header d-flex align-items-center sticky-top";

  var logoText = isIndex ? "APEX" : "APEX Group";

  // On index page, keep in-page anchors for Home/About to match original behavior.
  var homeHref = isIndex ? "#hero" : "index.html#hero";
  var aboutHref = isIndex ? "#about" : "index.html#about";

  function activeClass(key) {
    return key === activeKey ? ' class="active"' : "";
  }

  mount.innerHTML =
    '<header id="header" class="' +
    headerClass +
    '">' +
    '<div class="container-fluid container-xl position-relative d-flex align-items-center">' +
    '<a href="index.html" class="logo d-flex align-items-center me-auto">' +
    "<h1 class=\"sitename\">" +
    logoText +
    "</h1>" +
    "</a>" +
    '<nav id="navmenu" class="navmenu">' +
    "<ul>" +
    '<li><a href="' +
    homeHref +
    '"' +
    activeClass("home") +
    ">Home</a></li>" +
    '<li><a href="' +
    aboutHref +
    '"' +
    activeClass("about") +
    ">About</a></li>" +
    '<li><a href="team.html"' +
    activeClass("team") +
    ">Team</a></li>" +
    '<li><a href="publications.html"' +
    activeClass("publications") +
    ">Publications</a></li>" +
    '<li><a href="portfolio.html"' +
    activeClass("portfolio") +
    ">Portfolio</a></li>" +
    '<li><a href="misc.html"' +
    activeClass("misc") +
    ">MISC</a></li>" +
    "</ul>" +
    '<i class="mobile-nav-toggle d-xl-none bi bi-list"></i>' +
    "</nav>" +
    "</div>" +
    "</header>";
})();


