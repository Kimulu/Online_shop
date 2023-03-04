function updateCartIcon() {
var cartCount = document.getElementById('cart-count');
var itemCount = 0;
fetch('/get_cart_items_count') // Send a GET request to the server to get the cart items count
.then(response => response.json()) // Parse the JSON response from the server
.then(data => {
  itemCount = data.count; // Update the item count with the response data
  cartCount.innerText = itemCount; // Update the cart icon
});
}

function updateCartIcon2() {
  var cartCount = document.getElementById('cart-count2');
  var itemCount = 0;
  fetch('/get_cart_items_count') // Send a GET request to the server to get the cart items count
  .then(response => response.json()) // Parse the JSON response from the server
  .then(data => {
    itemCount = data.count; // Update the item count with the response data
    cartCount.innerText = itemCount; // Update the cart icon
  });
  }

$(document).ready(function() {
  $(".alert").fadeTo(2000, 500).slideUp(1000, function(){
    $(".alert").slideUp(500);
  });
});

