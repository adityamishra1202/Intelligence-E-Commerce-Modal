// Product catalog for the Amazon Clone (ShopZone)
const productsData = [
  {
    id: 1,
    title: "Apple iPhone 15 Pro (128 GB) - Natural Titanium",
    category: "Electronics",
    price: 999.00,
    originalPrice: 1099.00,
    rating: 4.8,
    reviewsCount: 14280,
    isPrime: true,
    badge: "Best Seller",
    image: "https://images.unsplash.com/photo-1695048133142-1a20484d2569?auto=format&fit=crop&w=600&q=80",
    images: [
      "https://images.unsplash.com/photo-1695048133142-1a20484d2569?auto=format&fit=crop&w=600&q=80",
      "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?auto=format&fit=crop&w=600&q=80"
    ],
    description: "Forged in titanium and featuring the groundbreaking A17 Pro chip, a customizable Action button, and the most powerful iPhone camera system ever.",
    features: [
      "Strong and lightweight aerospace-grade titanium design",
      "6.1-inch Super Retina XDR display with ProMotion up to 120Hz",
      "A17 Pro chip delivers next-level mobile gaming performance",
      "48MP Main camera for super-high-resolution photos"
    ],
    inStock: true
  },
  {
    id: 2,
    title: "Sony WH-1000XM5 Wireless Noise Canceling Headphones",
    category: "Electronics",
    price: 328.00,
    originalPrice: 399.99,
    rating: 4.7,
    reviewsCount: 9540,
    isPrime: true,
    badge: "Amazon's Choice",
    image: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80",
    images: [
      "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80",
      "https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=600&q=80"
    ],
    description: "Industry-leading noise cancellation optimized to you. Magnificently engineered for magnificent sound with Auto NC Optimizer.",
    features: [
      "Up to 30-hour battery life with quick charging (3 min for 3 hours of playback)",
      "Crystal clear hands-free calling with 4 beamforming microphones",
      "Multipoint connection allows quick switching between devices",
      "Intuitive touch control settings"
    ],
    inStock: true
  },
  {
    id: 3,
    title: "Apple 2024 MacBook Air 13-inch Laptop with M3 chip",
    category: "Computers",
    price: 1049.00,
    originalPrice: 1199.00,
    rating: 4.9,
    reviewsCount: 5120,
    isPrime: true,
    badge: "Limited time deal",
    image: "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=600&q=80",
    images: [
      "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=600&q=80"
    ],
    description: "Lean, mean, M3 machine. Built for Apple Intelligence. Strikingly thin, fast, and provides up to 18 hours of battery life.",
    features: [
      "Supercharged by the next-generation M3 chip with an 8-core CPU",
      "Liquid Retina display supports 1 billion colors",
      "1080p FaceTime HD camera, three mics, and four speakers with Spatial Audio",
      "MagSafe charging port, two Thunderbolt ports, and headphone jack"
    ],
    inStock: true
  },
  {
    id: 4,
    title: "PlayStation 5 Digital Edition Console (Slim)",
    category: "Gaming",
    price: 449.99,
    originalPrice: 499.99,
    rating: 4.9,
    reviewsCount: 22410,
    isPrime: true,
    badge: "Best Seller",
    image: "https://images.unsplash.com/photo-1606813907291-d86efa9b94db?auto=format&fit=crop&w=600&q=80",
    images: [
      "https://images.unsplash.com/photo-1606813907291-d86efa9b94db?auto=format&fit=crop&w=600&q=80"
    ],
    description: "Experience lightning-fast loading with an ultra-high speed SSD, deeper immersion with haptic feedback, adaptive triggers and 3D Audio.",
    features: [
      "Slim Design: Packed with powerful gaming technology in a sleek chassis",
      "1TB of built-in ultra-fast SSD storage",
      "Ray Tracing and up to 120fps with 120Hz output",
      "Includes DualSense wireless controller"
    ],
    inStock: true
  },
  {
    id: 5,
    title: "Logitech MX Master 3S Wireless Performance Mouse",
    category: "Computers",
    price: 89.99,
    originalPrice: 99.99,
    rating: 4.8,
    reviewsCount: 18230,
    isPrime: true,
    badge: "Amazon's Choice",
    image: "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?auto=format&fit=crop&w=600&q=80",
    images: [
      "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?auto=format&fit=crop&w=600&q=80"
    ],
    description: "An icon remastered. Feel every moment of your workflow with even more precision, tactility, and performance, thanks to Quiet Clicks and an 8K DPI track-on-glass sensor.",
    features: [
      "Quiet Clicks deliver satisfying, soft tactile feel with 90% less click noise",
      "MagSpeed electromagnetic scrolling is 90% faster and 87% more precise",
      "Ergonomic silhouette crafted to support your palm and fingers",
      "Flow cross-computer control across Windows and macOS"
    ],
    inStock: true
  },
  {
    id: 6,
    title: "Nike Air Max 270 Men's Running Shoes - Triple Black",
    category: "Fashion",
    price: 129.50,
    originalPrice: 160.00,
    rating: 4.6,
    reviewsCount: 7420,
    isPrime: true,
    badge: "",
    image: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=600&q=80",
    images: [
      "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=600&q=80"
    ],
    description: "Boasting Nike's biggest heel Air unit yet, the Nike Air Max 270 delivers visible air under every step with a sleek, super-breathable modern upper.",
    features: [
      "Large Max Air unit delivers responsive, all-day cushioning",
      "Knit fabric on the upper provides a lightweight fit and airy feel",
      "Stretchy inner sleeve creates a snug, sock-like fit",
      "Durable rubber outsole delivers traction where you need it"
    ],
    inStock: true
  },
  {
    id: 7,
    title: "Nespresso VertuoPlus Coffee and Espresso Machine by De'Longhi",
    category: "Home & Kitchen",
    price: 139.95,
    originalPrice: 169.00,
    rating: 4.7,
    reviewsCount: 16750,
    isPrime: true,
    badge: "Deal of the Day",
    image: "https://images.unsplash.com/photo-1517668808822-9ebb02ae2a0e?auto=format&fit=crop&w=600&q=80",
    images: [
      "https://images.unsplash.com/photo-1517668808822-9ebb02ae2a0e?auto=format&fit=crop&w=600&q=80"
    ],
    description: "Single-serve coffee maker using Centrifusion technology to gently brew both coffee and authentic espresso at the touch of a button.",
    features: [
      "Brews 4 cup sizes: 5oz and 8oz coffee, and single and double espresso",
      "Automatic capsule ejection and fast heat-up in 20-25 seconds",
      "Extra-large 60 oz. water reservoir can pivot to fit counter space",
      "Complimentary starter pack of Nespresso capsules included"
    ],
    inStock: true
  },
  {
    id: 8,
    title: "Apple Watch Ultra 2 [GPS + Cellular 49mm] Smartwatch",
    category: "Electronics",
    price: 749.00,
    originalPrice: 799.00,
    rating: 4.9,
    reviewsCount: 3890,
    isPrime: true,
    badge: "Amazon's Choice",
    image: "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?auto=format&fit=crop&w=600&q=80",
    images: [
      "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?auto=format&fit=crop&w=600&q=80"
    ],
    description: "The ultimate sports and adventure watch. Powered by S9 SiP with a brightest display ever, precision dual-frequency GPS, and up to 36 hours of battery life.",
    features: [
      "Rugged 49mm corrosion-resistant titanium case",
      "Up to 3,000 nits peak brightness for outdoor visibility",
      "Precision dual-frequency GPS provides remarkable accuracy",
      "Water resistance 100m; tested to MIL-STD 810H"
    ],
    inStock: true
  },
  {
    id: 9,
    title: "Classic Minimalist Chronograph Leather Watch for Men",
    category: "Fashion",
    price: 68.00,
    originalPrice: 110.00,
    rating: 4.5,
    reviewsCount: 3200,
    isPrime: true,
    badge: "Limited time deal",
    image: "https://images.unsplash.com/photo-1524805444758-089113d48a6d?auto=format&fit=crop&w=600&q=80",
    images: [
      "https://images.unsplash.com/photo-1524805444758-089113d48a6d?auto=format&fit=crop&w=600&q=80"
    ],
    description: "A timeless, understated wristwatch featuring a genuine Italian leather strap, stainless steel case, and precise Japanese quartz movement.",
    features: [
      "Japanese Quartz Movement with analog display",
      "Scratch-resistant mineral crystal glass lens",
      "Genuine supple top-grain leather strap with buckle closure",
      "Water-resistant to 30m (100ft)"
    ],
    inStock: true
  },
  {
    id: 10,
    title: "Instant Pot Duo 7-in-1 Electric Pressure Cooker, 6 Quart",
    category: "Home & Kitchen",
    price: 84.99,
    originalPrice: 99.99,
    rating: 4.8,
    reviewsCount: 89400,
    isPrime: true,
    badge: "Best Seller",
    image: "https://images.unsplash.com/photo-1588854337236-6889d631faa8?auto=format&fit=crop&w=600&q=80",
    images: [
      "https://images.unsplash.com/photo-1588854337236-6889d631faa8?auto=format&fit=crop&w=600&q=80"
    ],
    description: "Replaces 7 kitchen appliances: pressure cooker, slow cooker, rice cooker, steamer, sauté pan, yogurt maker & food warmer. Cooks up to 70% faster.",
    features: [
      "13 customizable Smart Programs for one-touch cooking",
      "Fingerprint-resistant stainless steel sides and dishwasher-safe lid",
      "Includes over 10 safety features plus overheat protection",
      "Capacity cooks for up to 6 people"
    ],
    inStock: true
  },
  {
    id: 11,
    title: "Kindle Paperwhite (16 GB) – Now with 6.8\" display and warm light",
    category: "Electronics",
    price: 139.99,
    originalPrice: 149.99,
    rating: 4.8,
    reviewsCount: 42100,
    isPrime: true,
    badge: "Amazon's Choice",
    image: "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80",
    images: [
      "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80"
    ],
    description: "Now with a 6.8” display, thinner borders, adjustable warm light, up to 10 weeks of battery life, and 20% faster page turns.",
    features: [
      "Flush-front design and 300 ppi glare-free display that reads like real paper",
      "Adjustable warm light to shift screen shade from white to amber",
      "Waterproof (IPX8) so you're free to read at the beach or in the bath",
      "Stores thousands of books with 16GB internal capacity"
    ],
    inStock: true
  },
  {
    id: 12,
    title: "Dyson V15 Detect Cordless Vacuum Cleaner",
    category: "Home & Kitchen",
    price: 629.99,
    originalPrice: 749.99,
    rating: 4.7,
    reviewsCount: 6510,
    isPrime: true,
    badge: "Limited time deal",
    image: "https://images.unsplash.com/photo-1558317374-067fb5f30001?auto=format&fit=crop&w=600&q=80",
    images: [
      "https://images.unsplash.com/photo-1558317374-067fb5f30001?auto=format&fit=crop&w=600&q=80"
    ],
    description: "Dyson's most intelligent cordless vacuum. Engineered for whole-home deep cleaning with laser illumination revealing invisible dust.",
    features: [
      "Laser reveals microscopic dust on hard floors",
      "A piezo sensor continuously sizes and counts dust particles",
      "Up to 60 minutes of run time with click-in battery",
      "Hair screw tool cleans long hair and pet hair without tangling"
    ],
    inStock: true
  },
  {
    id: 13,
    title: "Ray-Ban Classic Polarized Aviator Sunglasses",
    category: "Fashion",
    price: 172.00,
    originalPrice: 221.00,
    rating: 4.6,
    reviewsCount: 11200,
    isPrime: true,
    badge: "Amazon's Choice",
    image: "https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=600&q=80",
    images: [
      "https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=600&q=80"
    ],
    description: "An iconic silhouette designed originally for U.S. aviators. Crisp optical clarity with polarized crystal lenses that block 100% UV rays.",
    features: [
      "100% UV400 protection coating",
      "Legendary metal frame with comfortable silicone nose pads",
      "Polarized lenses eliminate glare and reflection",
      "Includes protective leather case and microfiber cleaning cloth"
    ],
    inStock: true
  },
  {
    id: 14,
    title: "Razer BlackWidow V4 Mechanical RGB Gaming Keyboard",
    category: "Gaming",
    price: 119.99,
    originalPrice: 169.99,
    rating: 4.7,
    reviewsCount: 4890,
    isPrime: true,
    badge: "Best Seller",
    image: "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=600&q=80",
    images: [
      "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=600&q=80"
    ],
    description: "Full-blown battlestation immersion with mechanical switches, dedicated macro keys, multi-function roller, and per-key Razer Chroma RGB.",
    features: [
      "Razer Green Clicky Mechanical Switches for precise tactical feedback",
      "6 dedicated macro keys for programmable shortcuts",
      "Multi-function roller and 4 media keys for convenient control",
      "Magnetic plush leatherette wrist rest for gaming comfort"
    ],
    inStock: true
  },
  {
    id: 15,
    title: "Anker 737 Power Bank (PowerCore 24K), 140W 3-Port Portable Charger",
    category: "Electronics",
    price: 99.99,
    originalPrice: 149.99,
    rating: 4.8,
    reviewsCount: 8320,
    isPrime: true,
    badge: "Deal of the Day",
    image: "https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?auto=format&fit=crop&w=600&q=80",
    images: [
      "https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?auto=format&fit=crop&w=600&q=80"
    ],
    description: "Equipped with the latest Power Delivery 3.1 and bi-directional technology to quickly recharge the portable charger or get a 140W ultra-powerful charge.",
    features: [
      "Ultra-Powerful Two-Way Charging with 140W max output",
      "Smart digital display shows output and input power and estimated time",
      "Huge 24,000mAh capacity juices up iPhone 13 almost 5 times",
      "Compact design with ActiveShield 2.0 temperature protection"
    ],
    inStock: true
  },
  {
    id: 16,
    title: "Ceramic Minimalist Indoor Plant Pot Set with Drainage (3 Pack)",
    category: "Home & Kitchen",
    price: 34.99,
    originalPrice: 45.00,
    rating: 4.6,
    reviewsCount: 3820,
    isPrime: true,
    badge: "",
    image: "https://images.unsplash.com/photo-1485955900006-10f4d324d411?auto=format&fit=crop&w=600&q=80",
    images: [
      "https://images.unsplash.com/photo-1485955900006-10f4d324d411?auto=format&fit=crop&w=600&q=80"
    ],
    description: "Modern matte finish ceramic pots designed with minimalist lines, bamboo saucers, and mesh drainage hole screens to elevate any living space.",
    features: [
      "Includes three graduating sizes (4.2\", 5.3\", 6.5\")",
      "High temperature fired ceramic with smooth matte glaze",
      "Drainage holes prevent root rot and overwatering",
      "Natural bamboo trays catch excess runoff"
    ],
    inStock: true
  }
];

// Banner slide data
const heroBanners = [
  {
    id: 1,
    title: "Mega Electronics & Tech Sale",
    subtitle: "Up to 45% off the latest smartphones, laptops & accessories",
    tag: "Limited Time Deals",
    bgGradient: "linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)",
    cta: "Shop Tech Deals",
    categoryFilter: "Electronics"
  },
  {
    id: 2,
    title: "Upgrade Your Home Sanctuary",
    subtitle: "Premium cookware, smart appliances & cozy home essentials",
    tag: "Exclusive Offers",
    bgGradient: "linear-gradient(135deg, #2b5876 0%, #4e4376 100%)",
    cta: "Explore Home",
    categoryFilter: "Home & Kitchen"
  },
  {
    id: 3,
    title: "Level Up Your Gaming Battlestation",
    subtitle: "Next-gen consoles, mechanical keyboards, headsets & high-refresh gear",
    tag: "Gamer Fest 2026",
    bgGradient: "linear-gradient(135deg, #1f1c2c 0%, #928dab 100%)",
    cta: "Shop Gaming",
    categoryFilter: "Gaming"
  },
  {
    id: 4,
    title: "New Season Fashion & Footwear",
    subtitle: "Discover statement pieces, premium watches & everyday athletic wear",
    tag: "Trending Now",
    bgGradient: "linear-gradient(135deg, #141e30 0%, #243b55 100%)",
    cta: "Discover Fashion",
    categoryFilter: "Fashion"
  }
];

// 4-Card Quad promos shown on hero overlay (Classic Amazon layout)
const promoCards = [
  {
    title: "Gaming & Accessories",
    linkText: "See all gaming items",
    category: "Gaming",
    items: [
      { name: "Consoles", img: "https://images.unsplash.com/photo-1606813907291-d86efa9b94db?auto=format&fit=crop&w=260&q=80" },
      { name: "Keyboards", img: "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=260&q=80" },
      { name: "Mice", img: "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?auto=format&fit=crop&w=260&q=80" },
      { name: "Headsets", img: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=260&q=80" }
    ]
  },
  {
    title: "Refresh Your Living Space",
    linkText: "Shop home essentials",
    category: "Home & Kitchen",
    items: [
      { name: "Kitchen", img: "https://images.unsplash.com/photo-1588854337236-6889d631faa8?auto=format&fit=crop&w=260&q=80" },
      { name: "Coffee", img: "https://images.unsplash.com/photo-1517668808822-9ebb02ae2a0e?auto=format&fit=crop&w=260&q=80" },
      { name: "Cleaning", img: "https://images.unsplash.com/photo-1558317374-067fb5f30001?auto=format&fit=crop&w=260&q=80" },
      { name: "Decor", img: "https://images.unsplash.com/photo-1485955900006-10f4d324d411?auto=format&fit=crop&w=260&q=80" }
    ]
  },
  {
    title: "Top Deals in Electronics",
    linkText: "Explore more electronics",
    category: "Electronics",
    items: [
      { name: "Smartphones", img: "https://images.unsplash.com/photo-1695048133142-1a20484d2569?auto=format&fit=crop&w=260&q=80" },
      { name: "Smartwatches", img: "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?auto=format&fit=crop&w=260&q=80" },
      { name: "E-Readers", img: "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=260&q=80" },
      { name: "Audio", img: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=260&q=80" }
    ]
  },
  {
    title: "Trending Styles & Footwear",
    linkText: "Discover fashion trends",
    category: "Fashion",
    items: [
      { name: "Sneakers", img: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=260&q=80" },
      { name: "Watches", img: "https://images.unsplash.com/photo-1524805444758-089113d48a6d?auto=format&fit=crop&w=260&q=80" },
      { name: "Eyewear", img: "https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=260&q=80" },
      { name: "Apparel", img: "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=260&q=80" }
    ]
  }
];
