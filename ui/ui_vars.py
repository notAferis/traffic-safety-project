BODY_HTML = r"""
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;600;700;900&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">

<style>

    /* Custom theme styles matching tailwind-config extend */
    .bg-background { background-color: #0d1516 !important; }
    .bg-background\/80 { background-color: rgba(13, 21, 22, 0.8) !important; }
    .bg-surface-container { background-color: #192122 !important; }
    .bg-surface-container-low { background-color: #151d1e !important; }
    .bg-surface-container-high { background-color: #242b2d !important; }
    .bg-surface-container-highest { background-color: #2e3638 !important; }
    .bg-surface-variant { background-color: #2e3638 !important; }

    .text-primary { color: #c3f5ff !important; }
    .text-secondary { color: #ffcf8f !important; }
    .text-tertiary { color: #ffe7e2 !important; }
    .text-error { color: #ffb4ab !important; }

    .bg-primary { background-color: #c3f5ff !important; }
    .bg-secondary { background-color: #ffcf8f !important; }
    .bg-error { background-color: #93000a !important; }

    .border-outline-variant { border-color: #3b494c !important; }
    .outline-variant { border-color: #3b494c !important; }
    .text-on-primary { color: #00363d !important; }
    .text-on-secondary { color: #452b00 !important; }
    .text-on-surface { color: #dce4e5 !important; }
    .text-on-surface-variant { color: #bac9cc !important; }

    /* Opacity and fraction mappings */
    .bg-primary\/40 { background-color: rgba(195, 245, 255, 0.4) !important; }
    .bg-primary\/60 { background-color: rgba(195, 245, 255, 0.6) !important; }
    .bg-primary\/80 { background-color: rgba(195, 245, 255, 0.8) !important; }
    .bg-primary\/30 { background-color: rgba(195, 245, 255, 0.3) !important; }
    .bg-primary\/12 { background-color: rgba(195, 245, 255, 0.12) !important; }
    .bg-primary\/5 { background-color: rgba(195, 245, 255, 0.05) !important; }
    .bg-secondary\/10 { background-color: rgba(255, 207, 143, 0.1) !important; }
    .bg-secondary\/12 { background-color: rgba(255, 207, 143, 0.12) !important; }
    .bg-secondary\/20 { background-color: rgba(255, 207, 143, 0.2) !important; }
    .bg-secondary\/5 { background-color: rgba(255, 207, 143, 0.05) !important; }
    .bg-tertiary\/12 { background-color: rgba(255, 231, 226, 0.12) !important; }
    .bg-error\/10 { background-color: rgba(255, 180, 171, 0.1) !important; }
    .bg-error\/12 { background-color: rgba(255, 180, 171, 0.12) !important; }
    .border-primary\/20 { border-color: rgba(195, 245, 255, 0.2) !important; }
    .border-secondary\/20 { border-color: rgba(255, 207, 143, 0.2) !important; }
    .border-error\/20 { border-color: rgba(255, 180, 171, 0.2) !important; }
    .bg-surface-variant\/10 { background-color: rgba(46, 54, 56, 0.1) !important; }
    .bg-surface-variant\/20 { background-color: rgba(46, 54, 56, 0.2) !important; }
    .bg-surface-container-high\/50 { background-color: rgba(36, 43, 45, 0.5) !important; }
    .bg-surface-container-high\/30 { background-color: rgba(36, 43, 45, 0.3) !important; }
    .bg-surface-container-high\/20 { background-color: rgba(36, 43, 45, 0.2) !important; }
    .bg-surface-container-low\/60 { background-color: rgba(21, 29, 30, 0.6) !important; }
    .border-outline-variant\/30 { border-color: rgba(59, 73, 76, 0.6) !important; }
    .text-on-surface-variant\/60 { color: rgba(186, 201, 204, 0.6) !important; }
    .text-on-surface-variant\/40 { color: rgba(186, 201, 204, 0.4) !important; }
    .shadow-primary\/20 { box-shadow: 0 4px 14px rgba(195, 245, 255, 0.2) !important; }

    /* Elevation system */
    .shadow-card {
        box-shadow:
            0 1px 1px rgba(0, 0, 0, 0.3),
            0 8px 20px -8px rgba(0, 0, 0, 0.55),
            inset 0 1px 0 rgba(255, 255, 255, 0.02) !important;
    }

    /* Icon chip */
    .icon-chip {
        width: 34px;
        height: 34px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .icon-chip .material-symbols-outlined {
        font-size: 18px !important;
    }

    .gap-gutter { gap: 16px !important; }
    .gap-md { gap: 16px !important; }
    .p-lg { padding: 24px !important; }
    .p-md { padding: 16px !important; }
    .py-lg { padding-top: 24px !important; padding-bottom: 24px !important; }
    .px-lg { padding-left: 24px !important; padding-right: 24px !important; }
    .px-md { padding-left: 16px !important; padding-right: 16px !important; }
    .py-md { padding-top: 16px !important; padding-bottom: 16px !important; }
    .pt-lg { padding-top: 24px !important; }
    .pt-md { padding-top: 16px !important; }
    .mb-xl { margin-bottom: 32px !important; }
    .mb-lg { margin-bottom: 24px !important; }
    .mb-md { margin-bottom: 16px !important; }
    .mt-xl { margin-top: 32px !important; }
    .mt-lg { margin-top: 24px !important; }
    .w-sidebar-width { width: 260px !important; }
    .space-y-gutter > * + * { margin-top: 20px !important; }
    .space-y-md > * + * { margin-top: 16px !important; }
    .border-x {
        border-left-width: 1px !important;
        border-right-width: 1px !important;
        border-left-style: solid !important;
        border-right-style: solid !important;
    }

    /* Typography custom styles matching tailwind-config fontSize & fontFamily */
    .font-headline-sm { font-family: 'Hanken Grotesk', 'Inter', sans-serif !important; font-weight: 600 !important; }
    .text-headline-sm { font-size: 18px !important; line-height: 1.4 !important; }
    .font-headline-lg { font-family: 'Hanken Grotesk', 'Inter', sans-serif !important; font-weight: 600 !important; }
    .text-headline-lg { font-size: 24px !important; line-height: 1.3 !important; }
    .font-headline-xl { font-family: 'Hanken Grotesk', 'Inter', sans-serif !important; font-weight: 700 !important; }
    .text-headline-xl { font-size: 36px !important; line-height: 1.2 !important; letter-spacing: -0.02em !important; }
    .font-body-sm { font-family: 'Hanken Grotesk', 'Inter', sans-serif !important; font-weight: 400 !important; }
    .text-body-sm { font-size: 12px !important; line-height: 1.5 !important; }
    .font-body-md { font-family: 'Hanken Grotesk', 'Inter', sans-serif !important; font-weight: 400 !important; }
    .text-body-md { font-size: 14px !important; line-height: 1.6 !important; }
    .font-label-mono { font-family: 'JetBrains Mono', monospace !important; font-weight: 500 !important; }
    .text-label-mono { font-size: 12px !important; line-height: 1 !important; letter-spacing: 0.05em !important; }
    .font-label-caps { font-family: 'JetBrains Mono', monospace !important; font-weight: 700 !important; }
    .text-label-caps { font-size: 11px !important; line-height: 1 !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; }

    /* Material Symbols font settings */
    .material-symbols-outlined {
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        display: inline-block;
        vertical-align: middle;
    }

    /* Global page resets */
    html, body, [data-testid="stHeader"] {
        font-family: 'Hanken Grotesk', 'Inter', sans-serif !important;
        background-color: #0d1516 !important;
        color: #dce4e5 !important;
    }
    [data-testid="stAppViewContainer"] {
        font-family: 'Hanken Grotesk', 'Inter', sans-serif !important;
        color: #dce4e5 !important;
        background: #0d1516 !important;
    }

    /* Redesigned Streamlit Sidebar */
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

    .material-symbols-outlined {
        font-family: 'Material Symbols Outlined' !important;
        font-weight: normal !important;
        font-style: normal !important;
        display: inline-block !important;
        line-height: 1 !important;
        text-transform: none !important;
        letter-spacing: normal !important;
        word-wrap: normal !important;
        white-space: nowrap !important;
        direction: ltr !important;
        -webkit-font-smoothing: antialiased !important;
    }

    [data-testid="stSidebar"] {
        background-color: #151d1e !important;
        border-right: 1px solid #3b494c !important;
        width: 270px !important;
        min-width: 270px !important;
    }
    [data-testid="stSidebar"] > div:first-child,
    [data-testid="stSidebarContent"] {
        background-color: #151d1e !important;
        display: flex !important;
        flex-direction: column !important;
        height: 100vh !important;
        padding: 1.25rem 0.75rem !important;
        box-sizing: border-box !important;
    }

    /* Pure CSS Flexbox Sequencing: Brand (1), Nav (10), Footer (999) */
    [data-testid="stSidebarUserContent"] {
        display: contents !important;
        order: 1 !important;
    }
    [data-testid="stSidebarUserContent"] > div,
    [data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"] {
        display: contents !important;
    }

    /* 1. Brand Top: Order 1 */
    [data-testid="stSidebarContent"] [data-testid="stElementContainer"]:has(.sidebar-brand-top),
    [data-testid="stSidebarUserContent"] [data-testid="stElementContainer"]:has(.sidebar-brand-top),
    div:has(> div > .sidebar-brand-top),
    div:has(> .sidebar-brand-top),
    .sidebar-brand-top {
        order: 1 !important;
        width: 100% !important;
    }

    /* 2. Navigation Tabs Container: Order 10 */
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarContent"] > div:first-child,
    [data-testid="stSidebarContent"] > div:has([data-testid="stSidebarNav"]) {
        order: 10 !important;
        width: 100% !important;
        padding: 0 4px !important;
        margin-top: 8px !important;
        margin-bottom: auto !important;
    }
    [data-testid="stSidebarNav"] ul {
        display: flex !important;
        flex-direction: column !important;
        gap: 12px !important; /* Spaced out tabs */
        padding: 12px 0 !important;
        margin: 0 !important;
    }
    [data-testid="stSidebarNav"] li {
        padding: 0 !important;
        margin: 0 !important;
        list-style: none !important;
    }
    [data-testid="stSidebarNav"] a,
    [data-testid="stSidebarNavLink"] {
        display: flex !important;
        align-items: center !important;
        gap: 14px !important;
        padding: 12px 16px !important; /* Generous tab padding */
        color: #bac9cc !important;
        font-family: 'Hanken Grotesk', sans-serif !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        border-left: 4px solid transparent !important;
        background-color: transparent !important;
        text-decoration: none !important;
        transition: color 0.2s ease, background-color 0.2s ease, border-color 0.2s ease, transform 0.15s ease !important;
    }
    [data-testid="stSidebarNav"] a:hover,
    [data-testid="stSidebarNavLink"]:hover {
        color: #dce4e5 !important;
        background-color: #2e3638 !important;
    }
    [data-testid="stSidebarNav"] a:active,
    [data-testid="stSidebarNavLink"]:active {
        transform: scale(0.98) !important;
    }
    /* Active State styling */
    [data-testid="stSidebarNav"] a[aria-current="page"],
    [data-testid="stSidebarNav"] a[data-testid="stSidebarNavLinkActive"],
    [data-testid="stSidebarNav"] a:has([aria-current="page"]) {
        background-color: rgba(255, 255, 255, 0.06) !important;
        border-left: 4px solid #c3f5ff !important;
        color: #c3f5ff !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] span,
    [data-testid="stSidebarNav"] a[data-testid="stSidebarNavLinkActive"] span,
    [data-testid="stSidebarNav"] a:has([aria-current="page"]) span {
        color: #c3f5ff !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebarNav"] span {
        font-family: 'Hanken Grotesk', 'Inter', sans-serif !important;
    }

    [data-testid="stSidebarContent"] [data-testid="stElementContainer"]:has(.sidebar-footer-bottom),
    [data-testid="stSidebarUserContent"] [data-testid="stElementContainer"]:has(.sidebar-footer-bottom),
    div:has(> div > .sidebar-footer-bottom),
    .sidebar-footer-bottom {
        order: 999 !important;
        margin-top: auto !important;
        width: 100% !important;
    }

    /* Set maximum width of the app container */
    [data-testid="stAppViewBlockContainer"] {
        padding: 16px 24px !important;
        max-width: 100% !important;
    }

    /* Streamlit's default gap between stacked widgets (~1rem) compounds fast
       down a long control panel — tighten it app-wide. */
    [data-testid="stVerticalBlock"] {
        gap: 0.6rem !important;
    }

    /* Bordered containers (the tabs card, etc.) get generous default padding
       from Streamlit — tighten it to match the rest of this tighter layout. */
    div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"] {
        gap: 0.6rem !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 4px !important;
    }

    /* Tabs: slimmer tab bar, less dead space above/below the active panel */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 4px !important;
    }
    [data-testid="stTabs"] button[data-baseweb="tab"] {
        padding: 8px 12px !important;
        height: auto !important;
    }
    [data-testid="stTabs"] [data-testid="stVerticalBlock"] {
        gap: 0.5rem !important;
    }
    [data-testid="stTabsPanel"] {
        padding-top: 10px !important;
    }

    /* Expander: tighter body padding */
    [data-testid="stExpanderDetails"] {
        padding-top: 6px !important;
    }

    /* Sidebar Radio Navigation styling */
    [data-testid="stSidebar"] [data-testid="stRadio"] > div {
        gap: 8px !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        background-color: #161c1e !important;
        border: 1px solid #263134 !important;
        border-radius: 10px !important;
        padding: 12px 14px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #eef2f3 !important;
        cursor: pointer !important;
        transition: all 0.2s ease-in-out !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background-color: #212a2d !important;
        border-color: #4cd7f6 !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"],
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
        background-color: rgba(76, 215, 246, 0.18) !important;
        border-color: #4cd7f6 !important;
        color: #4cd7f6 !important;
        font-weight: 700 !important;
        box-shadow: 0 0 10px rgba(76, 215, 246, 0.2) !important;
    }

    /* Widget labels app-wide */
    label, [data-testid="stWidgetLabel"] p {
        color: #9fadb2 !important;
        font-size: 12px !important;
        font-weight: 500 !important;
    }

    /* Style select box, text input and number input app-wide (control panel
       lives in a regular column, not st.sidebar, so these can't be scoped
       to [data-testid="stSidebar"] the way they used to be) */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] {
        background-color: #0e1214 !important;
        border: 1px solid #263134 !important;
        border-radius: 10px !important;
        color: #eef2f3 !important;
        transition: border-color 0.15s ease-in-out !important;
    }
    div[data-baseweb="select"]:focus-within > div,
    div[data-baseweb="input"]:focus-within {
        border-color: #4cd7f6 !important;
    }
    div[data-baseweb="input"] > input {
        color: #eef2f3 !important;
    }
    /* The select/combobox popover menu renders in a portal at document body,
       outside the themed container, so it needs its own explicit dark styling */
    div[data-baseweb="popover"] ul,
    div[data-baseweb="menu"] {
        background-color: #171d1f !important;
        border: 1px solid #263134 !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="popover"] li,
    div[data-baseweb="menu"] li {
        color: #eef2f3 !important;
    }
    div[data-baseweb="popover"] li:hover,
    div[data-baseweb="menu"] li:hover {
        background-color: #2b3538 !important;
    }

    /* Bordered containers (st.container(border=True)) styled as cards to
       match the Live Feed / Log Console panels elsewhere on the page */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(180deg, #151b1d 0%, #12171a 100%) !important;
        border: 1px solid #263134 !important;
        border-radius: 16px !important;
        margin-bottom: 16px !important;
        box-shadow:
            0 1px 1px rgba(0, 0, 0, 0.3),
            0 8px 20px -8px rgba(0, 0, 0, 0.55),
            inset 0 1px 0 rgba(255, 255, 255, 0.02) !important;
    }

    /* Expander styled as a nested card inside a control-panel section */
    [data-testid="stExpander"] {
        background-color: #0e1214 !important;
        border: 1px solid #263134 !important;
        border-radius: 12px !important;
    }
    [data-testid="stExpander"] summary {
        border-radius: 12px !important;
    }

    /* The native floating current-value bubble on sliders is redundant with
       the custom value label rendered next to each slider's title */
    div[data-testid="stSliderThumbValue"] {
        display: none !important;
    }

    /* Custom styles for Streamlit sliders */
    div[data-testid="stSlider"] [role="slider"] {
        background-color: #4cd7f6 !important;
        box-shadow: 0 0 10px rgba(76, 215, 246, 0.4) !important;
        border: none !important;
    }
    div[data-testid="stSlider"] div[data-baseweb="slider"] > div > div {
        background: #263134 !important;
    }
    div[data-testid="stSlider"] div[data-baseweb="slider"] > div > div > div {
        background-color: #4cd7f6 !important;
    }

    /* Toggle switches use the theme's primaryColor (config.toml) for their
       checked state by default, which already matches the app's cyan accent. */

    /* Style file uploader dropzone */
    [data-testid="stFileUploader"] {
        background-color: #0e1214 !important;
        border: 1px dashed #263134 !important;
        border-radius: 12px !important;
        padding: 8px !important;
    }
    [data-testid="stFileUploader"] section {
        background-color: transparent !important;
        padding: 0 !important;
    }
    [data-testid="stFileUploader"] label {
        display: none !important;
    }

    /* Custom styles for Streamlit buttons */
    div.stButton > button {
        width: 100% !important;
        border-radius: 10px !important;
        padding: 12px 20px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        transition: all 0.15s ease-in-out !important;
    }

    /* Primary button style */
    div.stButton > button[kind="primary"] {
        background-color: #4cd7f6 !important;
        color: #003640 !important;
        border: none !important;
        box-shadow: 0 4px 16px rgba(76, 215, 246, 0.28) !important;
    }
    div.stButton > button[kind="primary"]:hover {
        opacity: 0.92 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(76, 215, 246, 0.36) !important;
    }

    /* Secondary button style — neutral by default (e.g. "Add Camera Feed") */
    div.stButton > button[kind="secondary"] {
        background-color: #171d1f !important;
        color: #eef2f3 !important;
        border: 1px solid #263134 !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #212a2d !important;
        border-color: #4cd7f6 !important;
    }

    /* Destructive actions (Stop Stream, Remove Feed) — scoped via a keyed
       st.container() wrapper so only these secondary buttons render red,
       instead of every secondary button app-wide */
    [class*="st-key-stop-stream-btn"] div.stButton > button[kind="secondary"],
    [class*="st-key-feed-remove-"] div.stButton > button[kind="secondary"] {
        background-color: #7a0009 !important;
        color: #ffdad6 !important;
        border: 1px solid #ff8a80 !important;
    }
    [class*="st-key-stop-stream-btn"] div.stButton > button[kind="secondary"]:hover,
    [class*="st-key-feed-remove-"] div.stButton > button[kind="secondary"]:hover {
        opacity: 0.92 !important;
        transform: translateY(-1px) !important;
        background-color: #93000a !important;
        border-color: #ff8a80 !important;
    }

    /* Frame boundaries */
    [data-testid="stImage"] img {
        border-left: 1px solid #263134 !important;
        border-right: 1px solid #263134 !important;
        border-radius: 0 !important;
    }

    /* Scrollbars configuration */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #12171a;
    }
    ::-webkit-scrollbar-thumb {
        background: #263134;
        border-radius: 10px;
    }
</style>

<script>
    const forceSidebarOpen = () => {
        try {
            // Force Streamlit internal session storage state to expanded
            window.localStorage.setItem('streamlit::sidebarCollapsed', 'false');
            window.sessionStorage.setItem('streamlit::sidebarCollapsed', 'false');
            
            // Programmatically query the parent or main document's collapsed control button and click it
            const doc = window.parent.document || document;
            const expandButton = doc.querySelector('[data-testid="collapsedControl"] button') || doc.querySelector('[data-testid="collapsedControl"]');
            if (expandButton) {
                expandButton.click();
            }
        } catch (e) {
            console.error("Failed to force sidebar open:", e);
        }
    };
    // Run immediately and after short delays to ensure DOM is fully ready
    forceSidebarOpen();
    setTimeout(forceSidebarOpen, 300);
    setTimeout(forceSidebarOpen, 1000);
</script>

"""

SIDEBAR_HEADER_HTML = """
<div class="px-md mb-md mt-1 flex items-center gap-3">
    <div class="icon-chip bg-primary/12">
        <span class="material-symbols-outlined text-primary" style="font-variation-settings: 'FILL' 1;">analytics</span>
    </div>
    <div>
        <h1 class="text-body-md font-headline-sm text-on-surface m-0" style="font-weight: 600;">AI Command Center</h1>
        <p class="text-body-sm font-body-sm text-on-surface-variant/60 m-0">v2.4.0-stable</p>
    </div>
</div>
"""

TOP_HEADER_TEMPLATE = """
<header class="w-full py-4 px-lg flex justify-between items-center bg-surface-container-low/60 backdrop-blur-md border border-outline-variant/30 rounded-2xl shadow-card mb-4">
    <div class="flex items-center gap-4">
        <div class="w-11 h-11 rounded-2xl flex items-center justify-center bg-primary/12 border border-primary/20">
            <span class="material-symbols-outlined text-primary" style="font-size: 24px;">shield_with_heart</span>
        </div>
        <div>
            <h2 class="text-headline-lg font-headline-lg font-bold text-on-surface tracking-tight m-0">Smart Traffic Monitor</h2>
            <p class="text-body-sm font-body-sm text-on-surface-variant/60 m-0">AI-assisted incident detection and emergency dispatch</p>
        </div>
    </div>
    <div class="flex items-center gap-3">
        <span class="px-3 py-1.5 {dispatch_badge_bg} {dispatch_badge_color} text-[10px] font-bold rounded-full border {dispatch_badge_border} flex items-center gap-1.5 uppercase tracking-wider">
            <span class="material-symbols-outlined" style="font-size: 13px;">{dispatch_icon}</span> {dispatch_label}
        </span>
        <span class="px-3 py-1.5 bg-surface-container-high text-on-surface-variant text-[11px] font-label-mono rounded-full border border-outline-variant">
            {clock_display}
        </span>
    </div>
</header>
"""

METRICS_TEMPLATE = """
<div class="grid grid-cols-1 md:grid-cols-4 gap-gutter mb-4">
    <!-- Card 1: System Status -->
    <div class="bg-surface-container-low border border-outline-variant p-lg rounded-2xl shadow-card">
        <div class="flex items-center justify-between mb-4">
            <div class="icon-chip bg-primary/12">
                <span class="material-symbols-outlined text-primary">sensors</span>
            </div>
            <div class="w-2.5 h-2.5 rounded-full {status_animate}" style="background-color: {status_color}; {status_shadow}"></div>
        </div>
        <span class="text-label-caps font-label-caps text-on-surface-variant/60 uppercase tracking-widest block mb-1">System Status</span>
        <span class="text-headline-sm font-headline-sm text-on-surface">{status_text}</span>
    </div>

    <!-- Card 2: Input Source -->
    <div class="bg-surface-container-low border border-outline-variant p-lg rounded-2xl shadow-card">
        <div class="flex items-center justify-between mb-4">
            <div class="icon-chip bg-primary/12">
                <span class="material-symbols-outlined text-primary">movie</span>
            </div>
        </div>
        <span class="text-label-caps font-label-caps text-on-surface-variant/60 uppercase tracking-widest block mb-1">Input Source</span>
        <span class="text-headline-sm font-headline-sm text-on-surface">{source_display}</span>
    </div>

    <!-- Card 3: Surveillance FPS -->
    <div class="bg-surface-container-low border border-outline-variant p-lg rounded-2xl shadow-card">
        <div class="flex items-center justify-between mb-4">
            <div class="icon-chip bg-primary/12">
                <span class="material-symbols-outlined text-primary">speed</span>
            </div>
        </div>
        <span class="text-label-caps font-label-caps text-on-surface-variant/60 uppercase tracking-widest block mb-1">Surveillance FPS</span>
        <span class="text-headline-sm font-headline-sm text-primary font-mono">{fps_display}</span>
    </div>

    <!-- Card 4: Incident Alert -->
    <div class="bg-surface-container-low border border-outline-variant p-lg rounded-2xl shadow-card">
        <div class="flex items-center justify-between mb-4">
            <div class="icon-chip {alert_bg}">
                <span class="material-symbols-outlined {alert_color}">verified_user</span>
            </div>
        </div>
        <span class="text-label-caps font-label-caps text-on-surface-variant/60 uppercase tracking-widest block mb-1">Incident Alert</span>
        <span class="text-headline-sm font-headline-sm {alert_color}">{alert_text}</span>
    </div>
</div>
"""

LIVE_FEED_HEADER_TEMPLATE = """
<div class="bg-surface-container-low border-t border-x border-outline-variant rounded-t-2xl overflow-hidden shadow-card">
    <div class="px-lg py-4 border-b border-outline-variant flex items-center justify-between bg-surface-container-high/30">
        <div class="flex items-center gap-3">
            <div class="icon-chip bg-primary/12">
                <span class="material-symbols-outlined text-primary">videocam</span>
            </div>
            <h3 class="text-body-md font-headline-sm text-on-surface m-0" style="font-weight: 600;">Live Feed Monitor</h3>
        </div>
        <span class="px-3 py-1.5 {ai_badge_bg} {ai_badge_color} text-[10px] font-bold rounded-full border {ai_badge_border} flex items-center gap-1.5 uppercase tracking-wider">
            <span class="w-1.5 h-1.5 {ai_dot_bg} rounded-full {ai_dot_animate}"></span> AI Detection {ai_status_text}
        </span>
    </div>
</div>
"""

DEFAULT_PLACEHOLDER_HTML = """
<div class="w-full flex items-center justify-center border-x border-outline-variant bg-surface-container-low" style="height: 400px;">
    <div class="flex flex-col items-center justify-center p-6 text-center" style="max-width: 320px;">
        <div class="icon-chip bg-primary/12 mb-4" style="width: 52px; height: 52px; border-radius: 16px; margin-left: auto; margin-right: auto;">
            <span class="material-symbols-outlined text-primary" style="font-size: 26px;">videocam_off</span>
        </div>
        <p class="text-body-md text-on-surface-variant m-0">No feed running.<br/>Configure a camera feed and click 'Start Stream' in the control panel to begin detection.</p>
    </div>
</div>
"""

LIVE_FEED_FOOTER_TEMPLATE = """
<div class="p-md flex items-center justify-between bg-surface-container-high/20 border-x border-b border-outline-variant rounded-b-2xl mb-4 shadow-card">
    <div class="text-[10px] font-label-mono text-on-surface-variant/60 uppercase tracking-tighter">
        {feed_count_display}
    </div>
    <div class="text-[10px] font-label-mono text-on-surface-variant/40 uppercase tracking-tighter">
        CONFIDENCE THRESHOLD &ge; {threshold_display}
    </div>
</div>
"""

LOG_CONSOLE_TEMPLATE = """
<div class="bg-surface-container-low border border-outline-variant rounded-2xl shadow-card flex flex-col" style="height: 300px;">
    <div class="px-md py-3.5 border-b border-outline-variant flex items-center gap-3">
        <div class="icon-chip bg-primary/12" style="width: 28px; height: 28px; border-radius: 8px;">
            <span class="material-symbols-outlined text-primary" style="font-size: 15px;">list_alt</span>
        </div>
        <h3 class="text-label-caps font-label-caps text-on-surface-variant uppercase tracking-widest m-0">Incident Log Console</h3>
    </div>
    <div class="flex-1 overflow-y-auto p-md space-y-2 font-label-mono text-[11px]" style="height: 230px;">
        {logs_html}
    </div>
</div>
"""

STATS_CARD_TEMPLATE = """
<div class="bg-surface-container-low border border-outline-variant rounded-2xl shadow-card p-lg space-y-md">
    <div class="flex items-center gap-3 mb-1">
        <div class="icon-chip bg-primary/12" style="width: 28px; height: 28px; border-radius: 8px;">
            <span class="material-symbols-outlined text-primary" style="font-size: 15px;">analytics</span>
        </div>
        <h3 class="text-label-caps font-label-caps text-on-surface-variant uppercase tracking-widest m-0">Session Summary</h3>
    </div>
    <div class="grid grid-cols-2 gap-md">
        <div>
            <span class="text-body-sm text-on-surface-variant block mb-1">Session Time</span>
            <span class="text-headline-lg font-headline-lg text-on-surface font-mono">{elapsed_display}</span>
        </div>
        <div>
            <span class="text-body-sm text-on-surface-variant block mb-1">Frames Processed</span>
            <span class="text-headline-lg font-headline-lg text-on-surface font-mono">{frame_count:,}</span>
        </div>
    </div>
    <div class="space-y-1 pt-md border-t border-outline-variant/30">
        <div class="flex items-center justify-between py-1.5">
            <span class="text-body-sm text-on-surface-variant flex items-center gap-2.5">
                <div class="icon-chip bg-tertiary/12" style="width: 26px; height: 26px; border-radius: 7px;">
                    <span class="material-symbols-outlined text-tertiary" style="font-size: 14px;">warning</span>
                </div>
                Detector Flags
            </span>
            <span class="text-body-md text-on-surface" style="font-weight: 700;">{flags_count}</span>
        </div>
        <div class="flex items-center justify-between py-1.5">
            <span class="text-body-sm text-on-surface-variant flex items-center gap-2.5">
                <div class="icon-chip bg-error/12" style="width: 26px; height: 26px; border-radius: 7px;">
                    <span class="material-symbols-outlined text-error" style="font-size: 14px;">campaign</span>
                </div>
                Alerts Dispatched
            </span>
            <span class="text-body-md text-error" style="font-weight: 700;">{dispatched_count}</span>
        </div>
        <div class="flex items-center justify-between py-1.5">
            <span class="text-body-sm text-on-surface-variant flex items-center gap-2.5">
                <div class="icon-chip bg-secondary/12" style="width: 26px; height: 26px; border-radius: 7px;">
                    <span class="material-symbols-outlined text-secondary" style="font-size: 14px;">filter_alt</span>
                </div>
                False Alarms Filtered
            </span>
            <span class="text-body-md text-secondary" style="font-weight: 700;">{filtered_count}</span>
        </div>
    </div>
</div>
"""

DEFAULT_LOG_CONSOLE_HTML = """
<div class="bg-surface-container-low border border-outline-variant rounded-2xl shadow-card flex flex-col" style="height: 300px;">
    <div class="px-md py-3.5 border-b border-outline-variant flex items-center gap-3">
        <div class="icon-chip bg-primary/12" style="width: 28px; height: 28px; border-radius: 8px;">
            <span class="material-symbols-outlined text-primary" style="font-size: 15px;">list_alt</span>
        </div>
        <h3 class="text-label-caps font-label-caps text-on-surface-variant uppercase tracking-widest m-0">Incident Log Console</h3>
    </div>
    <div class="flex-1 overflow-y-auto p-md space-y-2 font-label-mono text-[11px]" style="height: 230px;">
        <div class="flex gap-2 text-on-surface-variant/40">
            <span>No feed running — start a stream to begin monitoring for incidents.</span>
        </div>
    </div>
</div>
"""

DEFAULT_STATS_CARD_HTML = """
<div class="bg-surface-container-low border border-outline-variant rounded-2xl shadow-card p-lg space-y-md">
    <div class="flex items-center gap-3 mb-1">
        <div class="icon-chip bg-primary/12" style="width: 28px; height: 28px; border-radius: 8px;">
            <span class="material-symbols-outlined text-primary" style="font-size: 15px;">analytics</span>
        </div>
        <h3 class="text-label-caps font-label-caps text-on-surface-variant uppercase tracking-widest m-0">Session Summary</h3>
    </div>
    <div class="grid grid-cols-2 gap-md">
        <div>
            <span class="text-body-sm text-on-surface-variant block mb-1">Session Time</span>
            <span class="text-headline-lg font-headline-lg text-on-surface-variant/40 font-mono">00:00</span>
        </div>
        <div>
            <span class="text-body-sm text-on-surface-variant block mb-1">Frames Processed</span>
            <span class="text-headline-lg font-headline-lg text-on-surface-variant/40 font-mono">0</span>
        </div>
    </div>
    <div class="space-y-1 pt-md border-t border-outline-variant/30">
        <div class="flex items-center justify-between py-1.5">
            <span class="text-body-sm text-on-surface-variant flex items-center gap-2.5">
                <div class="icon-chip bg-surface-variant/20" style="width: 26px; height: 26px; border-radius: 7px;">
                    <span class="material-symbols-outlined text-on-surface-variant/40" style="font-size: 14px;">warning</span>
                </div>
                Detector Flags
            </span>
            <span class="text-body-md text-on-surface-variant/40" style="font-weight: 700;">0</span>
        </div>
        <div class="flex items-center justify-between py-1.5">
            <span class="text-body-sm text-on-surface-variant flex items-center gap-2.5">
                <div class="icon-chip bg-surface-variant/20" style="width: 26px; height: 26px; border-radius: 7px;">
                    <span class="material-symbols-outlined text-on-surface-variant/40" style="font-size: 14px;">campaign</span>
                </div>
                Alerts Dispatched
            </span>
            <span class="text-body-md text-on-surface-variant/40" style="font-weight: 700;">0</span>
        </div>
        <div class="flex items-center justify-between py-1.5">
            <span class="text-body-sm text-on-surface-variant flex items-center gap-2.5">
                <div class="icon-chip bg-surface-variant/20" style="width: 26px; height: 26px; border-radius: 7px;">
                    <span class="material-symbols-outlined text-on-surface-variant/40" style="font-size: 14px;">filter_alt</span>
                </div>
                False Alarms Filtered
            </span>
            <span class="text-body-md text-on-surface-variant/40" style="font-weight: 700;">0</span>
        </div>
    </div>
</div>
"""
