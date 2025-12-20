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

function pay(){
   if(confirm("Bạn chắc chắn thanh toán không?")){
    fetch('/api/pay_spare_part',{
        method: 'post',

        headers:{
            "Content-Type": "application/json"
        },

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
}

function payRepair(repairFormId){
   if(confirm("Bạn chắc chắn thanh toán không?")){
    fetch('/api/pay_repair/'+repairFormId,{
        method: 'post',
        body: JSON.stringify({
            repair_form_id: repairFormId,
        }),
        headers:{
            "Content-Type": "application/json"
        },
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
}
document.querySelectorAll('.cart-icon').forEach(icon => {
    icon.addEventListener('click', function(e) {
        if (!isAuthenticated) {
            e.preventDefault();

            fetch('/flash-login-required', { method: 'POST' })
                .then(() => {
                    location.reload();
                });
        }
    });
});


function addComment(sparepartId) {
    const textarea = document.getElementById('commentId');
    if (!textarea) return;

    const content = textarea.value.trim();
    if (!content) {
        alert("Vui lòng nhập nội dung bình luận!");
        return;
    }


    event.preventDefault();

    fetch('/api/comments', {
        method: 'POST',
        body: JSON.stringify({
            sparepart_id: sparepartId,
            content: content
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 201) {

            location.reload();
        } else {
            alert(data.err_msg || "Không thể gửi bình luận. Vui lòng thử lại!");
        }
    })
    .catch(err => {
        console.error(err);
        alert("Lỗi kết nối. Vui lòng kiểm tra mạng!");
    });
}