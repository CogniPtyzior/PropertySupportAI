document.querySelectorAll("[data-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    const targetId = button.getAttribute("data-copy");
    const target = document.getElementById(targetId);
    if (!target) return;
    await navigator.clipboard.writeText(target.innerText.trim());
    const previous = button.innerText;
    button.innerText = "Copied";
    setTimeout(() => { button.innerText = previous; }, 1200);
  });
});
