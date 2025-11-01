document.addEventListener('DOMContentLoaded', function() {
    // ดึง element ที่จำเป็นมาใช้งาน
    const menuToggle = document.getElementById('menuToggle');
    const closeBtn = document.getElementById('closeBtn');
    const sideNav = document.getElementById('sideNav');
    const mainContainer = document.getElementById('mainContainer');

    // ฟังก์ชันสำหรับเปิดเมนู
    function openNav() {
        if (sideNav && mainContainer) {
            sideNav.classList.add('show');
            mainContainer.classList.add('menu-open');
        }
    }

    // ฟังก์ชันสำหรับปิดเมนู
    function closeNav() {
        if (sideNav && mainContainer) {
            sideNav.classList.remove('show');
            mainContainer.classList.remove('menu-open');
        }
    }

    // เมื่อปุ่ม 3 ขีด (menuToggle) ถูกคลิก ให้เปิดเมนู
    if (menuToggle) {
        menuToggle.addEventListener('click', openNav);
    }

    // เมื่อปุ่มกากบาท (closeBtn) ถูกคลิก ให้ปิดเมนู
    if (closeBtn) {
        closeBtn.addEventListener('click', closeNav);
    }

    // (UX Bonus) ปิดเมนูเมื่อคลิกที่พื้นที่มืดๆ ด้านนอก
    if (mainContainer) {
        mainContainer.addEventListener('click', function(event) {
            // เช็คว่าเมนูเปิดอยู่ และไม่ได้คลิกที่ตัวเมนูเอง
            if (sideNav.classList.contains('show') && event.target === mainContainer) {
                closeNav();
            }
        });
    }
});