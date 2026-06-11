import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});

async function sendChatQuestion(question, debug = false, createTicket = false, ticketRequestId = "") {
  const response = await fetch(`${apiBaseUrl}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      provider: "nebius",
      debug,
      createTicket,
      ticketRequestId: ticketRequestId || null,
    }),
  });

  if (!response.ok) {
    let detail = "";
    try {
      const errorBody = await response.json();
      detail = typeof errorBody.detail === "string" ? errorBody.detail : "";
    } catch {
      detail = "";
    }

    throw new Error(detail || "Support chat request failed.");
  }

  return response.json();
}

async function fetchTickets(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      params.set(key, value);
    }
  });
  const query = params.toString();
  const response = await fetch(`${apiBaseUrl}/tickets${query ? `?${query}` : ""}`);

  if (!response.ok) {
    throw new Error("Ticket list request failed.");
  }

  return response.json();
}

async function updateTicketStatus(ticketId, status) {
  const response = await fetch(`${apiBaseUrl}/tickets/${ticketId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ status }),
  });

  if (!response.ok) {
    let detail = "";
    try {
      const errorBody = await response.json();
      detail = typeof errorBody.detail === "string" ? errorBody.detail : "";
    } catch {
      detail = "";
    }

    throw new Error(detail || "Ticket update request failed.");
  }

  return response.json();
}

const translations = {
  en: {
    addToCart: "Add to cart",
    all: "All",
    backToCatalog: "Back to catalog",
    browseProducts: "Browse products",
    cart: "Cart",
    cartIsEmpty: "Cart is empty",
    close: "Close",
    closeCart: "Close cart",
    departmentNav: "Product departments",
    emptyCartCopy: "Add products from the catalog to build a local cart.",
    electronicsCatalog: "Electronics catalog",
    features: "Features",
    featured: "Featured",
    highestRated: "Highest rated",
    items: "items",
    loadCatalogError: "Catalog could not be loaded. Make sure the backend API is running.",
    loadingCatalog: "Loading catalog",
    loadingReviews: "Loading reviews",
    matchingProducts: "matching products",
    mostReviewed: "Most reviewed",
    noProductsFound: "No products found",
    price: "Price",
    priceHigh: "Price: high to low",
    priceLow: "Price: low to high",
    productContext: "Product context",
    productFacts: "Product facts",
    quantity: "Quantity",
    rating: "Rating",
    remove: "Remove",
    reviewCount: "Review count",
    reviewSamples: "Customer review samples",
    reviews: "Reviews",
    reviewsUnavailable: "Reviews could not be loaded.",
    noReviewSamples: "No clean customer review samples are available for this product yet.",
    search: "Search",
    searchPlaceholder: "Search products, brands, or categories",
    sort: "Sort",
    support: "Support",
    supportConsole: "Tickets",
    supportConsoleTitle: "Support tickets",
    supportCompatibilityPrompt: "Will this work with Bluetooth devices?",
    supportCreateTicket: "Create ticket",
    supportCreatingTicket: "Creating ticket...",
    supportDebugMode: "Developer mode",
    supportDebugPanel: "Developer trace",
    supportDraftPlaceholder: "Ask a support question",
    supportError: "Support chat could not be reached. Please make sure the backend is running.",
    supportIntro:
      "Ask about returns, setup, troubleshooting, compatibility, or any product in the catalog.",
    supportLoading: "Getting support answer...",
    supportNoMessages: "No support messages yet.",
    supportReturnsPrompt: "What is the return policy?",
    supportSend: "Send",
    supportSetupPrompt: "How do I set this product up?",
    supportSources: "Sources",
    supportTicketCreated: "Ticket created",
    supportTicketError: "Ticket could not be created. Please try again.",
    supportTitle: "Support chat",
    supportTroubleshootingPrompt: "My product will not power on.",
    supportRetrievedContext: "Retrieved context",
    stars: "stars",
    ticketConversation: "Conversation",
    ticketCreated: "Created",
    ticketEmpty: "No tickets match the current filters.",
    ticketFilters: "Ticket filters",
    ticketIssue: "Issue",
    ticketListError: "Tickets could not be loaded.",
    ticketLoading: "Loading tickets",
    ticketNotes: "Internal notes",
    ticketPriority: "Priority",
    ticketProduct: "Product",
    ticketSource: "Source",
    ticketStatus: "Status",
    ticketUpdateError: "Ticket could not be updated.",
    topControls: "Catalog controls",
    total: "Total",
    tryDifferentSearch: "Try a different search or department.",
  },
  fr: {
    addToCart: "Ajouter au panier",
    all: "Tout",
    backToCatalog: "Retour au catalogue",
    browseProducts: "Parcourir les produits",
    cart: "Panier",
    cartIsEmpty: "Le panier est vide",
    close: "Fermer",
    closeCart: "Fermer le panier",
    departmentNav: "Rayons de produits",
    emptyCartCopy: "Ajoutez des produits du catalogue pour constituer un panier local.",
    electronicsCatalog: "Catalogue electronique",
    features: "Caracteristiques",
    featured: "Mis en avant",
    highestRated: "Les mieux notes",
    items: "articles",
    loadCatalogError: "Impossible de charger le catalogue. Verifiez que l'API backend est demarree.",
    loadingCatalog: "Chargement du catalogue",
    loadingReviews: "Chargement des avis",
    matchingProducts: "produits correspondants",
    mostReviewed: "Les plus commentes",
    noProductsFound: "Aucun produit trouve",
    price: "Prix",
    priceHigh: "Prix : decroissant",
    priceLow: "Prix : croissant",
    productContext: "Contexte du produit",
    productFacts: "Informations produit",
    quantity: "Quantite",
    rating: "Note",
    remove: "Retirer",
    reviewCount: "Nombre d'avis",
    reviewSamples: "Extraits d'avis clients",
    reviews: "Avis",
    reviewsUnavailable: "Impossible de charger les avis.",
    noReviewSamples: "Aucun extrait d'avis client propre n'est encore disponible pour ce produit.",
    search: "Rechercher",
    searchPlaceholder: "Rechercher produits, marques ou categories",
    sort: "Trier",
    support: "Support",
    supportConsole: "Tickets",
    supportConsoleTitle: "Tickets support",
    supportCompatibilityPrompt: "Ce produit fonctionne-t-il avec les appareils Bluetooth ?",
    supportCreateTicket: "Creer un ticket",
    supportCreatingTicket: "Creation du ticket...",
    supportDebugMode: "Mode developpeur",
    supportDebugPanel: "Trace developpeur",
    supportDraftPlaceholder: "Posez une question au support",
    supportError: "Impossible de joindre le chat support. Verifiez que le backend est demarre.",
    supportIntro:
      "Posez une question sur les retours, l'installation, le depannage, la compatibilite ou un produit du catalogue.",
    supportLoading: "Recherche de la reponse du support...",
    supportNoMessages: "Aucun message de support pour le moment.",
    supportReturnsPrompt: "Quelle est la politique de retour ?",
    supportSend: "Envoyer",
    supportSetupPrompt: "Comment configurer ce produit ?",
    supportSources: "Sources",
    supportTicketCreated: "Ticket cree",
    supportTicketError: "Impossible de creer le ticket. Reessayez.",
    supportTitle: "Chat support",
    supportTroubleshootingPrompt: "Mon produit ne s'allume pas.",
    supportRetrievedContext: "Contexte retrouve",
    stars: "etoiles",
    ticketConversation: "Conversation",
    ticketCreated: "Cree",
    ticketEmpty: "Aucun ticket ne correspond aux filtres.",
    ticketFilters: "Filtres tickets",
    ticketIssue: "Probleme",
    ticketListError: "Impossible de charger les tickets.",
    ticketLoading: "Chargement des tickets",
    ticketNotes: "Notes internes",
    ticketPriority: "Priorite",
    ticketProduct: "Produit",
    ticketSource: "Source",
    ticketStatus: "Statut",
    ticketUpdateError: "Impossible de mettre a jour le ticket.",
    topControls: "Controles du catalogue",
    total: "Total",
    tryDifferentSearch: "Essayez une autre recherche ou un autre rayon.",
  },
};

const categoryLabels = {
  fr: {
    "Audio & Car": "Audio et auto",
    "Cables & Parts": "Cables et pieces",
    "Cameras & Optics": "Cameras et optique",
    "Computers & Storage": "Ordinateurs et stockage",
    "Mobile Accessories": "Accessoires mobiles",
  },
};

const cartStorageKey = "csagent.cart.v1";
const evalModeKey = "eval";
const supportModeKey = "support";

function getAppMode() {
  const mode = new URLSearchParams(window.location.search).get("_m") ?? "";
  if (mode === "e") {
    return evalModeKey;
  }
  if (mode === "s") {
    return supportModeKey;
  }
  return "customer";
}

function isDeveloperModeAllowed() {
  return getAppMode() === evalModeKey;
}

function isSupportModeAllowed() {
  return getAppMode() === supportModeKey;
}

function getInitialCartItems() {
  try {
    const savedCart = window.localStorage.getItem(cartStorageKey);
    if (!savedCart) {
      return {};
    }

    const parsedCart = JSON.parse(savedCart);
    if (!parsedCart || typeof parsedCart !== "object" || Array.isArray(parsedCart)) {
      return {};
    }

    return Object.fromEntries(
      Object.entries(parsedCart)
        .map(([productId, quantity]) => [productId, Number(quantity)])
        .filter(([, quantity]) => Number.isInteger(quantity) && quantity > 0),
    );
  } catch {
    return {};
  }
}

function getRouteFromHash() {
  const hash = window.location.hash;
  if (hash === "#/support/tickets" && isSupportModeAllowed()) {
    return { productId: null, category: null, supportConsole: true };
  }

  const productMatch = hash.match(/^#\/products\/(.+)$/);
  if (productMatch) {
    return { productId: decodeURIComponent(productMatch[1]), category: null, supportConsole: false };
  }

  const groupMatch = hash.match(/^#\/categories\/(.+)$/);
  if (groupMatch) {
    return { productId: null, category: decodeURIComponent(groupMatch[1]), supportConsole: false };
  }

  return { productId: null, category: null, supportConsole: false };
}

function App() {
  const [route, setRoute] = useState(getRouteFromHash);
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [isCatalogLoading, setIsCatalogLoading] = useState(true);
  const [catalogError, setCatalogError] = useState("");
  const [reviewsByProduct, setReviewsByProduct] = useState({});
  const [reviewsLoadingProductId, setReviewsLoadingProductId] = useState("");
  const [reviewsError, setReviewsError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [sortMode, setSortMode] = useState("featured");
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [ticketCreationMessageId, setTicketCreationMessageId] = useState("");
  const [supportTickets, setSupportTickets] = useState([]);
  const [ticketFilters, setTicketFilters] = useState({ status: "open", priority: "" });
  const [selectedTicketId, setSelectedTicketId] = useState("");
  const [isTicketListLoading, setIsTicketListLoading] = useState(false);
  const [ticketListError, setTicketListError] = useState("");
  const [ticketUpdateError, setTicketUpdateError] = useState("");
  const [chatError, setChatError] = useState("");
  const [isDeveloperModeAllowedState, setIsDeveloperModeAllowedState] =
    useState(isDeveloperModeAllowed);
  const [isSupportModeAllowedState, setIsSupportModeAllowedState] =
    useState(isSupportModeAllowed);
  const [isDeveloperMode, setIsDeveloperMode] = useState(isDeveloperModeAllowed);
  const [cartItems, setCartItems] = useState(getInitialCartItems);
  const [language, setLanguage] = useState("en");
  const text = translations[language];

  useEffect(() => {
    const handleHashChange = () => setRoute(getRouteFromHash());
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  useEffect(() => {
    const syncModeAccess = () => {
      const developerAllowed = isDeveloperModeAllowed();
      const supportAllowed = isSupportModeAllowed();
      setIsDeveloperModeAllowedState(developerAllowed);
      setIsSupportModeAllowedState(supportAllowed);
      setIsDeveloperMode(developerAllowed);
      if (!supportAllowed && window.location.hash === "#/support/tickets") {
        window.location.hash = "#/";
      } else {
        setRoute(getRouteFromHash());
      }
    };

    syncModeAccess();
    window.addEventListener("popstate", syncModeAccess);
    return () => window.removeEventListener("popstate", syncModeAccess);
  }, []);

  useEffect(() => {
    window.localStorage.setItem(cartStorageKey, JSON.stringify(cartItems));
  }, [cartItems]);

  useEffect(() => {
    if (!products.length) {
      return;
    }

    setCartItems((currentItems) =>
      Object.fromEntries(
        Object.entries(currentItems).filter(([productId]) =>
          products.some((product) => product.id === productId),
        ),
      ),
    );
  }, [products]);

  useEffect(() => {
    let isMounted = true;

    async function loadCatalog() {
      try {
        const [productsResponse, categoriesResponse] = await Promise.all([
          fetch(`${apiBaseUrl}/products`),
          fetch(`${apiBaseUrl}/categories`),
        ]);

        if (!productsResponse.ok || !categoriesResponse.ok) {
          throw new Error("Catalog API request failed.");
        }

        const [nextProducts, nextCategories] = await Promise.all([
          productsResponse.json(),
          categoriesResponse.json(),
        ]);

        if (isMounted) {
          setProducts(nextProducts);
          setCategories(nextCategories);
          setCatalogError("");
        }
      } catch {
        if (isMounted) {
          setCatalogError(text.loadCatalogError);
        }
      } finally {
        if (isMounted) {
          setIsCatalogLoading(false);
        }
      }
    }

    loadCatalog();

    return () => {
      isMounted = false;
    };
  }, [text.loadCatalogError]);

  const selectedProduct = useMemo(
    () => products.find((product) => product.id === route.productId),
    [products, route.productId],
  );

  useEffect(() => {
    if (!selectedProduct || reviewsByProduct[selectedProduct.id]) {
      return;
    }

    let isMounted = true;

    async function loadReviews() {
      setReviewsLoadingProductId(selectedProduct.id);
      setReviewsError("");

      try {
        const response = await fetch(`${apiBaseUrl}/products/${selectedProduct.id}/reviews`);
        if (!response.ok) {
          throw new Error("Review API request failed.");
        }
        const reviews = await response.json();
        if (isMounted) {
          setReviewsByProduct((currentReviews) => ({
            ...currentReviews,
            [selectedProduct.id]: reviews,
          }));
        }
      } catch {
        if (isMounted) {
          setReviewsError(text.reviewsUnavailable);
        }
      } finally {
        if (isMounted) {
          setReviewsLoadingProductId("");
        }
      }
    }

    loadReviews();

    return () => {
      isMounted = false;
    };
  }, [reviewsByProduct, selectedProduct, text.reviewsUnavailable]);

  useEffect(() => {
    if (!route.supportConsole) {
      return;
    }

    let isMounted = true;

    async function loadTickets() {
      setIsTicketListLoading(true);
      setTicketListError("");
      setTicketUpdateError("");

      try {
        const tickets = await fetchTickets(ticketFilters);
        if (isMounted) {
          setSupportTickets(tickets);
          setSelectedTicketId((currentTicketId) =>
            tickets.some((ticket) => ticket.id === currentTicketId)
              ? currentTicketId
              : tickets[0]?.id ?? "",
          );
        }
      } catch {
        if (isMounted) {
          setTicketListError(text.ticketListError);
        }
      } finally {
        if (isMounted) {
          setIsTicketListLoading(false);
        }
      }
    }

    loadTickets();

    return () => {
      isMounted = false;
    };
  }, [route.supportConsole, ticketFilters, text.ticketListError]);

  const groupCounts = useMemo(
    () =>
      products.reduce((counts, product) => {
        counts.set(product.category, (counts.get(product.category) ?? 0) + 1);
        return counts;
      }, new Map()),
    [products],
  );

  const navigationGroups = useMemo(
    () => categories.filter((category) => groupCounts.has(category.name)),
    [categories, groupCounts],
  );

  const visibleProducts = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();
    const filtered = products.filter((product) => {
      const matchesCategory = !route.category || product.category === route.category;
      const searchableText = [
        product.title,
        product.brand,
        product.category,
        product.subcategory,
        product.description,
      ]
        .join(" ")
        .toLowerCase();
      return matchesCategory && (!normalizedSearch || searchableText.includes(normalizedSearch));
    });

    return [...filtered].sort((a, b) => {
      if (sortMode === "price-low") {
        return a.price - b.price;
      }
      if (sortMode === "price-high") {
        return b.price - a.price;
      }
      if (sortMode === "rating") {
        return b.rating - a.rating || b.reviewCount - a.reviewCount;
      }
      if (sortMode === "reviews") {
        return b.reviewCount - a.reviewCount;
      }
      return 0;
    });
  }, [products, route.category, searchTerm, sortMode]);

  const cartProducts = useMemo(
    () =>
      Object.entries(cartItems)
        .map(([productId, quantity]) => ({
          product: products.find((product) => product.id === productId),
          quantity,
        }))
        .filter((item) => item.product && item.quantity > 0),
    [cartItems, products],
  );

  const cartCount = cartProducts.reduce((total, item) => total + item.quantity, 0);
  const cartTotal = cartProducts.reduce(
    (total, item) => total + item.product.price * item.quantity,
    0,
  );

  function addToCart(productId) {
    setCartItems((currentItems) => ({
      ...currentItems,
      [productId]: (currentItems[productId] ?? 0) + 1,
    }));
    setIsCartOpen(true);
    setIsChatOpen(false);
  }

  function updateCartQuantity(productId, quantity) {
    setCartItems((currentItems) => {
      const nextItems = { ...currentItems };
      if (quantity <= 0) {
        delete nextItems[productId];
      } else {
        nextItems[productId] = quantity;
      }
      return nextItems;
    });
  }

  function closeChatPanel() {
    setIsChatOpen(false);
    setChatMessages([]);
    setChatInput("");
    setChatError("");
    setIsChatLoading(false);
    setTicketCreationMessageId("");
  }

  async function submitChatQuestion(question) {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || isChatLoading) {
      return;
    }

    const userMessage = {
      id: `${Date.now()}-user`,
      role: "user",
      content: trimmedQuestion,
    };

    setChatMessages((currentMessages) => [...currentMessages, userMessage]);
    setChatInput("");
    setChatError("");
    setIsChatLoading(true);

    try {
      const chatResponse = await sendChatQuestion(trimmedQuestion, isDeveloperMode);
      const assistantMessage = {
        id: `${Date.now()}-assistant`,
        role: "assistant",
        question: trimmedQuestion,
        content: chatResponse.answer,
        citations: chatResponse.citations ?? [],
        retrievedContext: chatResponse.retrievedContext ?? [],
        handoff: chatResponse.handoff ?? null,
        createdTicket: chatResponse.createdTicket ?? null,
        ticketError: "",
        debug: chatResponse.debug ?? null,
      };
      setChatMessages((currentMessages) => [...currentMessages, assistantMessage]);
    } catch {
      setChatInput(trimmedQuestion);
      setChatError(text.supportError);
    } finally {
      setIsChatLoading(false);
    }
  }

  async function createTicketFromMessage(message) {
    if (!message.handoff?.canCreateTicket || ticketCreationMessageId) {
      return;
    }

    setTicketCreationMessageId(message.id);
    setChatError("");

    try {
      const chatResponse = await sendChatQuestion(
        message.question,
        isDeveloperMode,
        true,
        message.id,
      );
      setChatMessages((currentMessages) =>
        currentMessages.map((currentMessage) =>
          currentMessage.id === message.id
            ? {
                ...currentMessage,
                createdTicket: chatResponse.createdTicket ?? null,
                ticketError: chatResponse.createdTicket ? "" : text.supportTicketError,
              }
            : currentMessage,
        ),
      );
    } catch {
      setChatMessages((currentMessages) =>
        currentMessages.map((currentMessage) =>
          currentMessage.id === message.id
            ? { ...currentMessage, ticketError: text.supportTicketError }
            : currentMessage,
        ),
      );
    } finally {
      setTicketCreationMessageId("");
    }
  }

  async function handleTicketStatusChange(ticketId, status) {
    setTicketUpdateError("");

    try {
      const updatedTicket = await updateTicketStatus(ticketId, status);
      setSupportTickets((currentTickets) =>
        currentTickets.map((ticket) => (ticket.id === updatedTicket.id ? updatedTicket : ticket)),
      );
    } catch {
      setTicketUpdateError(text.ticketUpdateError);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#/">
          <span className="brand-mark">CS</span>
          <span>
            <strong>CSAgent Electronics</strong>
            <small>{text.electronicsCatalog}</small>
          </span>
        </a>
        <div className="header-controls" aria-label={text.topControls}>
          <label className="search-field">
            <span>{text.search}</span>
            <input
              type="search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder={text.searchPlaceholder}
            />
          </label>
          <label className="sort-field">
            <span>{text.sort}</span>
            <select value={sortMode} onChange={(event) => setSortMode(event.target.value)}>
              <option value="featured">{text.featured}</option>
              <option value="price-low">{text.priceLow}</option>
              <option value="price-high">{text.priceHigh}</option>
              <option value="rating">{text.highestRated}</option>
              <option value="reviews">{text.mostReviewed}</option>
            </select>
          </label>
        </div>
        <nav className="topbar-meta" aria-label={text.topControls}>
          <div className="language-toggle" aria-label="Language">
            <button
              className={language === "en" ? "active" : ""}
              type="button"
              onClick={() => setLanguage("en")}
            >
              EN
            </button>
            <button
              className={language === "fr" ? "active" : ""}
              type="button"
              onClick={() => setLanguage("fr")}
            >
              FR
            </button>
          </div>
          <button
            className="support-toggle"
            type="button"
            onClick={() => {
              if (isChatOpen) {
                closeChatPanel();
              } else {
                setIsChatOpen(true);
              }
              setIsCartOpen(false);
            }}
            aria-expanded={isChatOpen}
          >
            <ChatIcon />
            {text.support}
          </button>
          {isSupportModeAllowedState && (
            <a className="support-toggle" href="#/support/tickets">
              {text.supportConsole}
            </a>
          )}
          <button
            className="cart-toggle"
            type="button"
            onClick={() => {
              setIsCartOpen((isOpen) => !isOpen);
              setIsChatOpen(false);
            }}
          >
            <CartIcon />
            {text.cart}
            <span>{cartCount}</span>
          </button>
        </nav>
      </header>

      <CategoryNav
        groups={navigationGroups}
        groupCounts={groupCounts}
        activeCategory={route.category}
        language={language}
        text={text}
        totalProductCount={products.length}
      />

      <main>
        {route.supportConsole ? (
          <SupportConsole
            error={ticketListError}
            filters={ticketFilters}
            isLoading={isTicketListLoading}
            onFilterChange={setTicketFilters}
            onSelectTicket={setSelectedTicketId}
            onStatusChange={handleTicketStatusChange}
            selectedTicketId={selectedTicketId}
            text={text}
            tickets={supportTickets}
            updateError={ticketUpdateError}
          />
        ) : isCatalogLoading ? (
          <StatusMessage title={text.loadingCatalog} />
        ) : catalogError ? (
          <StatusMessage title={catalogError} />
        ) : selectedProduct ? (
          <ProductDetail
            language={language}
            product={selectedProduct}
            reviews={reviewsByProduct[selectedProduct.id] ?? []}
            reviewsError={reviewsError}
            reviewsLoading={reviewsLoadingProductId === selectedProduct.id}
            text={text}
            onAddToCart={addToCart}
          />
        ) : (
          <ProductGrid
            activeCategory={route.category}
            language={language}
            products={visibleProducts}
            text={text}
            onAddToCart={addToCart}
          />
        )}
      </main>

      {isCartOpen && (
        <CartPanel
          cartItems={cartProducts}
          cartTotal={cartTotal}
          text={text}
          onClose={() => setIsCartOpen(false)}
          onUpdateQuantity={updateCartQuantity}
        />
      )}

      {isChatOpen && (
        <SupportPanel
          error={chatError}
          inputValue={chatInput}
          isLoading={isChatLoading}
          isDeveloperModeAllowed={isDeveloperModeAllowedState}
          messages={chatMessages}
          isDeveloperMode={isDeveloperMode}
          selectedProduct={selectedProduct}
          text={text}
          onClose={closeChatPanel}
          onInputChange={setChatInput}
          onDeveloperModeChange={setIsDeveloperMode}
          onSubmit={submitChatQuestion}
          onCreateTicket={createTicketFromMessage}
          ticketCreationMessageId={ticketCreationMessageId}
        />
      )}
    </div>
  );
}

function SupportConsole({
  error,
  filters,
  isLoading,
  onFilterChange,
  onSelectTicket,
  onStatusChange,
  selectedTicketId,
  text,
  tickets,
  updateError,
}) {
  const selectedTicket = tickets.find((ticket) => ticket.id === selectedTicketId) ?? tickets[0];

  function updateFilter(name, value) {
    onFilterChange((currentFilters) => ({
      ...currentFilters,
      [name]: value,
    }));
  }

  return (
    <section className="support-console" aria-labelledby="support-console-title">
      <div className="page-heading">
        <div>
          <p className="eyebrow">{text.supportConsole}</p>
          <h1 id="support-console-title">{text.supportConsoleTitle}</h1>
        </div>
      </div>

      <div className="ticket-filter-bar" aria-label={text.ticketFilters}>
        <label>
          <span>{text.ticketStatus}</span>
          <select value={filters.status} onChange={(event) => updateFilter("status", event.target.value)}>
            <option value="">All</option>
            <option value="open">open</option>
            <option value="in_progress">in_progress</option>
            <option value="waiting_on_customer">waiting_on_customer</option>
            <option value="resolved">resolved</option>
          </select>
        </label>
        <label>
          <span>{text.ticketPriority}</span>
          <select value={filters.priority} onChange={(event) => updateFilter("priority", event.target.value)}>
            <option value="">All</option>
            <option value="low">low</option>
            <option value="normal">normal</option>
            <option value="high">high</option>
            <option value="urgent">urgent</option>
          </select>
        </label>
      </div>

      {isLoading ? (
        <StatusMessage title={text.ticketLoading} />
      ) : error ? (
        <StatusMessage title={error} />
      ) : tickets.length ? (
        <div className="ticket-console-layout">
          <div className="ticket-list" aria-label={text.supportConsoleTitle}>
            {tickets.map((ticket) => (
              <button
                className={ticket.id === selectedTicket?.id ? "active" : ""}
                key={ticket.id}
                type="button"
                onClick={() => onSelectTicket(ticket.id)}
              >
                <span>{ticket.id}</span>
                <strong>{ticket.summary}</strong>
                <small>
                  {ticket.priority} | {ticket.issueType} | {ticket.status}
                </small>
              </button>
            ))}
          </div>

          {selectedTicket && (
            <TicketDetail
              onStatusChange={onStatusChange}
              text={text}
              ticket={selectedTicket}
              updateError={updateError}
            />
          )}
        </div>
      ) : (
        <StatusMessage title={text.ticketEmpty} />
      )}
    </section>
  );
}

function TicketDetail({ onStatusChange, text, ticket, updateError }) {
  const createdAt = ticket.createdAt ? new Date(ticket.createdAt).toLocaleString() : "";
  const productLabel = ticket.product?.productTitle || ticket.product?.productId || "None";
  const canUpdate = ticket.source !== "seed";

  return (
    <article className="ticket-detail">
      <div className="ticket-detail-header">
        <div>
          <p className="eyebrow">{ticket.id}</p>
          <h2>{ticket.summary}</h2>
        </div>
        <span className={`ticket-priority ${ticket.priority}`}>{ticket.priority}</span>
      </div>

      <dl className="ticket-facts">
        <div>
          <dt>{text.ticketStatus}</dt>
          <dd>
            {canUpdate ? (
              <select
                value={ticket.status}
                onChange={(event) => onStatusChange(ticket.id, event.target.value)}
              >
                <option value="open">open</option>
                <option value="in_progress">in_progress</option>
                <option value="waiting_on_customer">waiting_on_customer</option>
                <option value="resolved">resolved</option>
              </select>
            ) : (
              ticket.status
            )}
          </dd>
        </div>
        <div>
          <dt>{text.ticketIssue}</dt>
          <dd>{ticket.issueType}</dd>
        </div>
        <div>
          <dt>{text.ticketProduct}</dt>
          <dd>{productLabel}</dd>
        </div>
        <div>
          <dt>{text.ticketSource}</dt>
          <dd>{ticket.source}</dd>
        </div>
        <div>
          <dt>{text.ticketCreated}</dt>
          <dd>{createdAt}</dd>
        </div>
      </dl>

      {updateError && <p className="support-error">{updateError}</p>}

      {ticket.handoff?.question && (
        <section className="ticket-section">
          <h3>{text.ticketConversation}</h3>
          <p>{ticket.handoff.question}</p>
          {ticket.handoff.escalationReason && <p>{ticket.handoff.escalationReason}</p>}
        </section>
      )}

      {ticket.internalNotes?.length > 0 && (
        <section className="ticket-section">
          <h3>{text.ticketNotes}</h3>
          <ul>
            {ticket.internalNotes.map((note, index) => (
              <li key={`${ticket.id}-note-${index}`}>{note}</li>
            ))}
          </ul>
        </section>
      )}
    </article>
  );
}

function translateCategory(categoryName, language) {
  return categoryLabels[language]?.[categoryName] ?? categoryName;
}

function CategoryNav({ groups, groupCounts, activeCategory, language, text, totalProductCount }) {
  return (
    <nav className="category-nav" aria-label={text.departmentNav}>
      <a className={!activeCategory ? "active" : ""} href="#/">
        <span className="category-label">{text.all}</span>
        <span className="category-count">{totalProductCount}</span>
      </a>
      {groups.map((group) => (
        <a
          className={activeCategory === group.name ? "active" : ""}
          href={`#/categories/${encodeURIComponent(group.name)}`}
          key={group.name}
          title={translateCategory(group.name, language)}
        >
          <span className="category-label">{translateCategory(group.name, language)}</span>
          <span className="category-count">{groupCounts.get(group.name)}</span>
        </a>
      ))}
    </nav>
  );
}

function StatusMessage({ title }) {
  return (
    <section className="catalog-view">
      <div className="empty-state">
        <h2>{title}</h2>
      </div>
    </section>
  );
}

function ProductGrid({
  products,
  activeCategory,
  language,
  text,
  onAddToCart,
}) {
  return (
    <section className="catalog-view" aria-labelledby="catalog-title">
      <div className="page-heading">
        <div>
          <p className="eyebrow">
            {activeCategory
              ? `${products.length} ${text.matchingProducts}`
              : text.electronicsCatalog}
          </p>
          <h1 id="catalog-title">
            {activeCategory ? translateCategory(activeCategory, language) : text.browseProducts}
          </h1>
        </div>
      </div>

      {products.length ? (
        <div className="product-grid">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} text={text} onAddToCart={onAddToCart} />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <h2>{text.noProductsFound}</h2>
          <p>{text.tryDifferentSearch}</p>
        </div>
      )}
    </section>
  );
}

function ProductCard({ product, text, onAddToCart }) {
  return (
    <article className="product-card">
      <a className="product-card-link" href={`#/products/${encodeURIComponent(product.id)}`}>
        <div className="product-image-frame">
          <img src={product.image} alt="" loading="lazy" />
        </div>
        <div className="product-card-body">
          <div className="product-meta-row">
            <span>{product.subcategory}</span>
            <span>
              {product.rating.toFixed(1)} {text.stars}
            </span>
          </div>
          <h2>{product.title}</h2>
          <p>{product.brand}</p>
          <div className="product-card-footer">
            <strong>{currency.format(product.price)}</strong>
            <span>
              {product.reviewCount.toLocaleString()} {text.reviews.toLowerCase()}
            </span>
          </div>
        </div>
      </a>
      <div className="product-card-actions">
        <button type="button" onClick={() => onAddToCart(product.id)}>
          {text.addToCart}
        </button>
      </div>
    </article>
  );
}

function ProductDetail({ language, product, reviews, reviewsError, reviewsLoading, text, onAddToCart }) {
  return (
    <section className="detail-view" aria-labelledby="product-title">
      <a className="back-link" href="#/">
        {text.backToCatalog}
      </a>

      <div className="detail-layout">
        <div className="detail-image-frame">
          <img src={product.image} alt="" />
        </div>

        <div className="detail-content">
          <nav className="product-breadcrumb" aria-label={text.productContext}>
            <span>{translateCategory(product.category, language)}</span>
            <span>{product.subcategory}</span>
            <span>{product.brand}</span>
          </nav>
          <h1 id="product-title">{product.title}</h1>

          <div className="detail-facts" aria-label={text.productFacts}>
            <div>
              <span>{text.price}</span>
              <strong>{currency.format(product.price)}</strong>
            </div>
            <div>
              <span>{text.rating}</span>
              <strong>{product.rating.toFixed(1)} / 5</strong>
            </div>
            <div>
              <span>{text.reviewCount}</span>
              <strong>{product.reviewCount.toLocaleString()}</strong>
            </div>
          </div>

          <button className="detail-cart-button" type="button" onClick={() => onAddToCart(product.id)}>
            {text.addToCart}
          </button>

          <p className="description">{product.description}</p>

          <section aria-labelledby="features-title" className="features-block">
            <h2 id="features-title">{text.features}</h2>
            <ul>
              {product.features.map((feature) => (
                <li key={feature}>{feature}</li>
              ))}
            </ul>
          </section>

          <ReviewsSection
            reviews={reviews}
            reviewsError={reviewsError}
            reviewsLoading={reviewsLoading}
            text={text}
          />
        </div>
      </div>
    </section>
  );
}

function ReviewsSection({ reviews, reviewsError, reviewsLoading, text }) {
  return (
    <section aria-labelledby="reviews-title" className="reviews-block">
      <div className="section-heading-row">
        <h2 id="reviews-title">{text.reviewSamples}</h2>
        {reviews.length > 0 && <span>{reviews.length}</span>}
      </div>

      {reviewsLoading ? (
        <p className="muted-copy">{text.loadingReviews}</p>
      ) : reviewsError ? (
        <p className="muted-copy">{reviewsError}</p>
      ) : reviews.length ? (
        <div className="review-list">
          {reviews.slice(0, 6).map((review) => (
            <article className="review-card" key={`${review.reviewId}-${review.asin}`}>
              <div className="review-card-header">
                <strong>{review.rating.toFixed(1)} / 5</strong>
                {review.verifiedPurchase && <span>Verified</span>}
              </div>
              {review.title && <h3>{review.title}</h3>}
              <p>{review.text}</p>
            </article>
          ))}
        </div>
      ) : (
        <p className="muted-copy">{text.noReviewSamples}</p>
      )}
    </section>
  );
}

function CartPanel({ cartItems, cartTotal, text, onClose, onUpdateQuantity }) {
  return (
    <aside className="cart-panel" aria-label={text.cart}>
      <div className="cart-panel-header">
        <div>
          <p className="eyebrow">{text.cart}</p>
          <h2>{cartItems.length ? `${cartItems.length} ${text.items}` : text.cartIsEmpty}</h2>
        </div>
        <button className="cart-close" type="button" onClick={onClose} aria-label={text.closeCart}>
          {text.close}
        </button>
      </div>

      {cartItems.length ? (
        <>
          <div className="cart-item-list">
            {cartItems.map(({ product, quantity }) => (
              <div className="cart-item" key={product.id}>
                <img src={product.image} alt="" />
                <div className="cart-item-body">
                  <h3>{product.title}</h3>
                  <p>{currency.format(product.price)}</p>
                  <div className="quantity-controls" aria-label={`${text.quantity}: ${product.title}`}>
                    <button
                      type="button"
                      onClick={() => onUpdateQuantity(product.id, quantity - 1)}
                    >
                      -
                    </button>
                    <input
                      aria-label={text.quantity}
                      min="1"
                      type="number"
                      value={quantity}
                      onChange={(event) =>
                        onUpdateQuantity(product.id, Number(event.target.value))
                      }
                    />
                    <button
                      type="button"
                      onClick={() => onUpdateQuantity(product.id, quantity + 1)}
                    >
                      +
                    </button>
                    <button
                      className="remove-button"
                      type="button"
                      onClick={() => onUpdateQuantity(product.id, 0)}
                    >
                      {text.remove}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="cart-total">
            <span>{text.total}</span>
            <strong>{currency.format(cartTotal)}</strong>
          </div>
        </>
      ) : (
        <p className="cart-empty-copy">{text.emptyCartCopy}</p>
      )}
    </aside>
  );
}

function SupportPanel({
  error,
  inputValue,
  isLoading,
  isDeveloperModeAllowed,
  isDeveloperMode,
  messages,
  selectedProduct,
  text,
  onClose,
  onDeveloperModeChange,
  onInputChange,
  onSubmit,
  onCreateTicket,
  ticketCreationMessageId,
}) {
  const starterPrompts = [
    text.supportReturnsPrompt,
    selectedProduct
      ? `${text.supportSetupPrompt} ${selectedProduct.title} (${selectedProduct.id})`
      : text.supportSetupPrompt,
    text.supportTroubleshootingPrompt,
    text.supportCompatibilityPrompt,
  ];
  const canSubmit = inputValue.trim().length > 0 && !isLoading;

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit(inputValue);
  }

  return (
    <aside className="support-panel" aria-label={text.supportTitle}>
      <div className="support-panel-header">
        <div>
          <p className="eyebrow">{text.support}</p>
          <h2>{text.supportTitle}</h2>
        </div>
        <button className="cart-close" type="button" onClick={onClose} aria-label={text.close}>
          {text.close}
        </button>
      </div>

      <div className="support-panel-body">
        <p>{text.supportIntro}</p>
        {selectedProduct && (
          <div className="support-product-context">
            <span>{text.productContext}</span>
            <strong>{selectedProduct.title}</strong>
          </div>
        )}
        <div className="support-message-list" aria-live="polite">
          {messages.length ? (
            messages.map((message) => (
              <article className={`support-message ${message.role}`} key={message.id}>
                <p>{message.content}</p>
                {message.role === "assistant" && (
                  <AssistantEvidence
                    isDeveloperMode={isDeveloperMode}
                    message={message}
                    onCreateTicket={onCreateTicket}
                    text={text}
                    ticketCreationMessageId={ticketCreationMessageId}
                  />
                )}
              </article>
            ))
          ) : (
            <div className="support-empty-state">
              <p className="support-empty-copy">{text.supportNoMessages}</p>
              <div className="support-starter-list">
                {starterPrompts.map((prompt) => (
                  <button
                    type="button"
                    key={prompt}
                    onClick={() => onInputChange(prompt)}
                    disabled={isLoading}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
        {error && <p className="support-error">{error}</p>}
        <form className="support-compose" onSubmit={handleSubmit}>
          {isDeveloperModeAllowed && (
            <label className="developer-mode-toggle">
              <input
                checked={isDeveloperMode}
                onChange={(event) => onDeveloperModeChange(event.target.checked)}
                type="checkbox"
              />
              <span>{text.supportDebugMode}</span>
            </label>
          )}
          <label className="support-input-field">
            <span>{text.support}</span>
            <textarea
              value={inputValue}
              onChange={(event) => onInputChange(event.target.value)}
              placeholder={text.supportDraftPlaceholder}
              rows="3"
              disabled={isLoading}
            />
          </label>
          <button className="support-send-button" type="submit" disabled={!canSubmit}>
            {text.supportSend}
          </button>
        </form>
        {isLoading && <p className="muted-copy">{text.supportLoading}</p>}
      </div>
    </aside>
  );
}

function AssistantEvidence({
  isDeveloperMode,
  message,
  onCreateTicket,
  text,
  ticketCreationMessageId,
}) {
  const citations = message.citations ?? [];
  const retrievedContext = message.retrievedContext ?? [];
  const debug = message.debug ?? null;
  const handoff = message.handoff ?? null;
  const isCreatingTicket = ticketCreationMessageId === message.id;

  if (!handoff && !isDeveloperMode) {
    return null;
  }

  if (!handoff && !citations.length && !retrievedContext.length && !debug) {
    return null;
  }

  return (
    <div className="assistant-evidence">
      {handoff?.canCreateTicket && (
        <div className="ticket-handoff">
          {message.createdTicket ? (
            <p>
              {text.supportTicketCreated}: <strong>{message.createdTicket.id}</strong>
            </p>
          ) : (
            <button
              type="button"
              onClick={() => onCreateTicket(message)}
              disabled={isCreatingTicket}
            >
              {isCreatingTicket ? text.supportCreatingTicket : text.supportCreateTicket}
            </button>
          )}
          {message.ticketError && <p className="support-ticket-error">{message.ticketError}</p>}
        </div>
      )}

      {isDeveloperMode && citations.length > 0 && (
        <div className="citation-list" aria-label={text.supportSources}>
          <h3>{text.supportSources}</h3>
          {citations.map((citation, index) => (
            <div className="citation-item" key={`${citation.chunkId ?? citation.sourcePath}-${index}`}>
              <strong>
                [{index + 1}] {citation.label ?? citation.sourceLabel ?? citation.sourcePath ?? "Source"}
              </strong>
              <span>{formatCitationMeta(citation)}</span>
              {citation.sourcePath && <code>{citation.sourcePath}</code>}
            </div>
          ))}
        </div>
      )}

      {isDeveloperMode && retrievedContext.length > 0 && (
        <details className="retrieved-context">
          <summary>{text.supportRetrievedContext}</summary>
          <div className="retrieved-context-list">
            {retrievedContext.map((context, index) => (
              <article
                className="retrieved-context-item"
                key={`${context.chunkId ?? context.sourcePath}-${index}`}
              >
                <strong>{context.label ?? context.sourceLabel ?? context.sourcePath ?? `Context ${index + 1}`}</strong>
                <span>{formatCitationMeta(context)}</span>
                {(context.snippet || context.text) && <p>{context.snippet ?? context.text}</p>}
              </article>
            ))}
          </div>
        </details>
      )}

      {isDeveloperMode && debug && (
        <details className="developer-trace">
          <summary>{text.supportDebugPanel}</summary>
          <dl>
            <div>
              <dt>Intent</dt>
              <dd>{debug.intent ?? "unknown"}</dd>
            </div>
            <div>
              <dt>Graph path</dt>
              <dd>{(debug.graphPath ?? []).join(" -> ") || "unknown"}</dd>
            </div>
            <div>
              <dt>Product hints</dt>
              <dd>{(debug.productHints ?? []).join(", ") || "none"}</dd>
            </div>
            <div>
              <dt>Retrieval query</dt>
              <dd>{debug.retrievalPlan?.query || "none"}</dd>
            </div>
            <div>
              <dt>Retrieval settings</dt>
              <dd>
                k={debug.retrievalPlan?.k ?? 0}, candidates=
                {debug.retrievalPlan?.candidateCount ?? 0}, provider=
                {debug.retrievalPlan?.provider ?? "unknown"}
              </dd>
            </div>
            <div>
              <dt>Context</dt>
              <dd>
                enough={String(debug.contextAssessment?.hasEnoughContext ?? false)},
                clarification={String(debug.contextAssessment?.needsClarification ?? false)}
              </dd>
            </div>
            <div>
              <dt>Doc types</dt>
              <dd>
                expected: {(debug.contextAssessment?.expectedDocTypes ?? []).join(", ") || "none"};
                returned: {(debug.contextAssessment?.returnedDocTypes ?? []).join(", ") || "none"}
              </dd>
            </div>
          </dl>
        </details>
      )}
    </div>
  );
}

function formatCitationMeta(source) {
  return [
    source.docType ?? source.documentType,
    source.policy ? `Policy: ${source.policy}` : "",
    source.productId ? `Product: ${source.productId}` : "",
    source.chunkId ? `Chunk: ${source.chunkId}` : "",
  ]
    .filter(Boolean)
    .join(" | ");
}

function ChatIcon() {
  return (
    <svg
      aria-hidden="true"
      className="cart-icon"
      fill="none"
      height="18"
      viewBox="0 0 24 24"
      width="18"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M4.5 5.8a3 3 0 0 1 3-3h9a3 3 0 0 1 3 3v6.8a3 3 0 0 1-3 3H10l-4.5 4v-4a3 3 0 0 1-1-2.2V5.8Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
      <path
        d="M8 8h8M8 11.5h5"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

function CartIcon() {
  return (
    <svg
      aria-hidden="true"
      className="cart-icon"
      fill="none"
      height="18"
      viewBox="0 0 24 24"
      width="18"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M6.3 6h15l-1.7 8.2a2 2 0 0 1-2 1.6H8.7a2 2 0 0 1-2-1.7L5.2 3.8H2.8"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
      <path
        d="M9.2 20.2h.1M17.2 20.2h.1"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="3"
      />
    </svg>
  );
}

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
