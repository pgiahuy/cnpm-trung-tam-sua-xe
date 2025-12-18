function addToCart(id,name,price){
    if (!isAuthenticated) {
        fetch('/flash-login-required', { method: 'POST' })
            .then(() => {
                window.location.href = '/login';
            });
        return;
    }

    event.preventDefault()
    fetch('/api/carts',{
        method: 'post',
        body: JSON.stringify({
            "id": id,
            "name": name,
            "unit_price": price
        }),
        headers: {
            "content-type": "application/json"
        }
    }).then(res => res.json()).then(data => {
        let d = document.getElementsByClassName("cart-counter");
        for(let e of d){
            e.innerText = data.total_quantity;
        }
    })
}



function updateCart(id, obj){
    fetch('/api/update-cart',{
        method: 'put',
        body: JSON.stringify({
            'id': id,
            'quantity': parseInt(obj.value)

        }),
        headers:{
            'Content-Type': 'application/json'
           }
   }).then(res => res.json()).then(data => {
    let d = document.getElementsByClassName('cart-counter');
        for(let e of d){
            e.innerText = data.total_quantity;
        }

     let d2 = document.getElementById('cart-amount');
     d2.innerText = new Intl.NumberFormat().format(data.total_amount) ;

   })

}


function deleteCart(id){
    if (confirm("Bạn chắc chắn xoá sản phẩm này không?") == true){
        fetch('/api/delete-cart/' + id,{
        method: 'delete',
        headers:{
            'Content-Type': 'application/json'
           }
   }).then(res => res.json()).then(data => {
    let d = document.getElementsByClassName('cart-counter');
        for(let e of d){
            e.innerText = data.total_quantity;
        }

     let e = document.getElementById('cart-amount');
     e.innerText = new Intl.NumberFormat().format(data.total_amount) ;

     let e2 = document.getElementById('product'+id);
     e2.style.display = "none"

   })

    }

}

//Thanh toán
function pay(repairFormId) {
    if (!confirm("Bạn chắc chắn thanh toán hóa đơn sửa chữa này không?")) {
        return;
    }

    fetch("/api/pay", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            repair_form_id: repairFormId
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.code === 200) {
            // Redirect sang trang VNPAY
            window.location.href = data.pay_url;
        } else {
            alert(data.msg || "Thanh toán thất bại");
        }
    })
    .catch(err => {
        console.error(err);
        alert("Lỗi hệ thống");
    });
}


document.querySelectorAll('.cart-icon').forEach(icon => {
    icon.addEventListener('click', function(e) {
        if (!isAuthenticated) {
            e.preventDefault(); // ngăn redirect tới /cart
            // Gửi POST để set flash
            fetch('/flash-login-required', { method: 'POST' })
                .then(() => {
                    // reload để flash xuất hiện ngay chỗ template đã include
                    location.reload();
                });
        }
    });
});


