const menuToggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('.main-nav');
if (menuToggle) {
  menuToggle.addEventListener('click', () => {
    const isOpen = nav.classList.toggle('open');
    menuToggle.setAttribute('aria-expanded', isOpen);
  });
}
const fileInput = document.querySelector('#portfolio_image');
if (fileInput) {
  fileInput.addEventListener('change', () => {
    const label = document.querySelector('.file-name');
    label.textContent = fileInput.files[0]?.name || 'No file chosen';
  });
}