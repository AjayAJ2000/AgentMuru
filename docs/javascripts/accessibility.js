function labelNavigationLandmarks() {
  const search = document.querySelector(".md-search[role='dialog']");
  search?.setAttribute("aria-label", "Search documentation");

  document.querySelectorAll("nav.md-nav").forEach((navigation, index) => {
    const labelId = navigation.getAttribute("aria-labelledby");
    const label = labelId ? document.getElementById(labelId) : null;
    const section = label?.textContent?.trim() || "Documentation";

    navigation.removeAttribute("aria-labelledby");
    navigation.setAttribute("aria-label", `${section} navigation ${index + 1}`);
  });
}

labelNavigationLandmarks();

if (typeof document$ !== "undefined") {
  document$.subscribe(labelNavigationLandmarks);
}
