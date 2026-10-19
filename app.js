document.addEventListener('DOMContentLoaded', function () {
  document.body.classList.add('visible');
  const loader = document.getElementById('pageLoader');
  if (loader) {
    loader.classList.add('hidden');
    setTimeout(function () {
      loader.remove();
    }, 350);
  }
});
