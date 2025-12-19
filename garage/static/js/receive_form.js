(function () {
    function qs(sel) { return document.querySelector(sel); }
    function qsa(sel) { return document.querySelectorAll(sel); }

    function show(sel) { const el = qs(sel); if (el) el.style.display = ''; }
    function hide(sel) { const el = qs(sel); if (el) el.style.display = 'none'; }

    function hideField(fieldId) {
        const el = document.getElementById(fieldId.replace('#', ''));
        if (!el) return;
        const group = el.closest('.form-group');
        if (group) group.style.display = 'none';
    }
    function showField(fieldId) {
        const el = document.getElementById(fieldId.replace('#', ''));
        if (!el) return;
        const group = el.closest('.form-group');
        if (group) group.style.display = '';
    }

    // 1. Receive type
    function getReceiveType() {
        const el = qs('input[name="receive_type"]:checked');
        return el ? el.value : 'walk_in';
    }

    function toggleReceiveType() {
        const type = getReceiveType();
        if (type === 'appointment') {
            show('.receive-appointment');
            hide('.receive-walkin');
        } else {
            hide('.receive-appointment');
            show('.receive-walkin');
        }
    }

    // 2. Khách cũ/mới
    function isNewCustomer() {
        return qs('input[name="is_new_customer"]:checked')?.checked || false;
    }

    function toggleCustomerType() {
        if (isNewCustomer()) {
            hideField('#customer_id');
            showField('#new_customer_name');
            showField('#new_customer_phone');
        } else {
            showField('#customer_id');
            hideField('#new_customer_name');
            hideField('#new_customer_phone');
        }
    }

    // 3. Xe cũ/mới
    function isNewVehicle() {
        return qs('input[name="is_new_vehicle"]:checked')?.checked || false;
    }

    function toggleVehicleType() {
        if (isNewVehicle()) {
            hideField('#vehicle_id');
            showField('#new_vehicle_plate');
            showField('#new_vehicle_type');
        } else {
            showField('#vehicle_id');
            hideField('#new_vehicle_plate');
            hideField('#new_vehicle_type');
        }
    }

    // 4. Load xe theo khách
    function loadVehicles(customerId, vehicleSelect, selectedVehicleId = null) {
        if (!customerId) {
            vehicleSelect.innerHTML = '<option value="">-- Chọn khách hàng trước --</option>';
            return;
        }

        vehicleSelect.innerHTML = '<option value="">-- Đang tải...</option>';

        fetch(`/vehicles/${customerId}`)
            .then(res => res.ok ? res.json() : Promise.reject('Lỗi tải xe'))
            .then(data => {
                vehicleSelect.innerHTML = '<option value="">-- Chọn xe --</option>';

                if (!data || data.length === 0) {
                    const opt = document.createElement('option');
                    opt.value = '';
                    opt.textContent = 'Khách hàng chưa có xe nào';
                    opt.disabled = true;
                    vehicleSelect.appendChild(opt);
                } else {
                    data.forEach(v => {
                        const opt = document.createElement('option');
                        opt.value = v.id;
                        opt.textContent = `${v.license_plate} (${v.vehicle_type})`;
                        if (v.id == selectedVehicleId) opt.selected = true;
                        vehicleSelect.appendChild(opt);
                    });
                }
            })
            .catch(() => {
                vehicleSelect.innerHTML = '<option value="">Lỗi tải xe</option>';
            });
    }

    // INIT
    document.addEventListener('DOMContentLoaded', function () {
        const receiveRadios = qsa('input[name="receive_type"]');
        const customerCheckbox = qsa('input[name="is_new_customer"]');
        const vehicleCheckbox = qsa('input[name="is_new_vehicle"]');

        receiveRadios.forEach(el => el.addEventListener('change', toggleReceiveType));
        customerCheckbox.forEach(el => el.addEventListener('change', toggleCustomerType));
        vehicleCheckbox.forEach(el => el.addEventListener('change', toggleVehicleType));

        // Trạng thái ban đầu
        toggleReceiveType();
        toggleCustomerType();
        toggleVehicleType();

        const customerSelect = qs('#customer_id');
        const vehicleSelect = qs('#vehicle_id');
        const vehicleIdInput = qs('input[name="vehicle_id"]'); // hidden hoặc select

        if (customerSelect && vehicleSelect) {
            customerSelect.addEventListener('change', function () {
                const selectedVehicleId = vehicleSelect.dataset.currentId || null;
                loadVehicles(this.value, vehicleSelect, selectedVehicleId);
            });

            // === QUAN TRỌNG: Khi EDIT → lấy vehicle_id hiện tại từ form ===
            const currentVehicleId = vehicleSelect.value || qs('input[name="vehicle_id"][type="hidden"]')?.value;

            if (customerSelect.value) {
                loadVehicles(customerSelect.value, vehicleSelect, currentVehicleId);
            }
        }

        // Nếu tick "Xe mới" → xóa chọn xe cũ
        if (qs('input[name="is_new_vehicle"]')) {
            qs('input[name="is_new_vehicle"]').addEventListener('change', function () {
                if (this.checked && vehicleSelect) {
                    vehicleSelect.value = '';
                }
            });
        }
    });
})();