# ShopZone - Amazon Clone Frontend 🛒

A pixel-perfect, high-performance Amazon clone built with **pure HTML5, CSS3, and modern JavaScript**. Featuring authentic Amazon Ember typography, Amazon's iconic dark & gold color scheme, responsive product grids, live search, and an interactive slide-over cart.

---

## 🚀 How to Run (Instant Setup)

### Option 1: Direct File Open (Fastest)
Simply double-click or open **[`index.html`](file:///d:/Amazon-Clone/index.html)** in any web browser (Chrome, Edge, Firefox, Safari).

### Option 2: Local Web Server
You can also launch a quick local server:
```powershell
# Using Python:
python -m http.server 3000

# Open in browser:
http://localhost:3000
```

---

## 🎨 Key Features

1. **Authentic Amazon Visuals & Typography**:
   - Signature Amazon dark navbars (`#131921` & `#232f3e`), warm gold search button (`#febd69`), and yellow CTA buttons (`#ffd814`).
   - Custom SVG Amazon smile arc arrow logo.
   - Amazon Ember font stack and layout spacing.

2. **Full E-Commerce Product Catalog**:
   - 16+ curated products across **Electronics, Computers, Gaming, Fashion, and Home & Kitchen**.
   - Real star ratings, review counts, Prime badges, and strike-through pricing with discount percentages.

3. **Interactive Shopping Cart**:
   - Slide-over cart drawer with live badge counter in the header.
   - Increment (`+`), decrement (`-`), and delete items.
   - Real-time subtotal calculation.
   - Cart data automatically saved to browser `localStorage`.

4. **Live Search & Category Filtering**:
   - Real-time product search by keyword as you type.
   - Department dropdown filtering & category pills.

5. **Amazon-Style Features**:
   - **Hero Carousel Banner**: Auto-sliding banners with smooth gradient blending into product cards.
   - **4-Card Feature Quads**: Amazon's iconic category entrance cards overlapping the hero banner.
   - **Today's Lightning Deals**: Horizontal scrolling deal carousel with live ticking countdown timer.
   - **Quick Look Modal**: Detailed product view with thumbnail image gallery, description, key specs, and instant "Add to Cart" / "Buy Now".
   - **Side Hamburger Drawer ("All" menu)**: Full left slide-out menu.
   - **Location Selector**: Modal to change delivery zip code.

---

## 🛠️ How to Customize

### 1. Changing the Brand Name
Open **`index.html`** and replace `ShopZone` with your desired name (e.g. `PrimeStore`, `Amastore`, `NexShop`).

### 2. Adding More Products
Open **`js/products.js`** and append a new product object to the `productsData` array:
```javascript
{
  id: 17,
  title: "Your Product Name",
  category: "Electronics", // "Electronics", "Computers", "Gaming", "Fashion", "Home & Kitchen"
  price: 99.99,
  originalPrice: 129.99,
  rating: 4.8,
  reviewsCount: 3400,
  isPrime: true,
  badge: "Best Seller", // Or "Limited time deal", "Amazon's Choice", or ""
  image: "https://your-image-url.jpg",
  images: ["https://your-image-url.jpg"],
  description: "Product summary...",
  features: ["Key bullet 1", "Key bullet 2"],
  inStock: true
}
```
