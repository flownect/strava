// ✅ CONFIGURATION AVEC VOTRE CLIENT ID
const CONFIG = {
    // 🔑 Votre Client ID Strava
    STRAVA_CLIENT_ID: '161590',
    
    // 🌐 Votre Project ID Firebase
    STRAVA_REDIRECT_URI: 'https://strava-jerome.web.app/callback.html',
    
    // 🔗 Votre URL ngrok actuelle
    API_BASE_URL: 'https://1455-78-245-248-89.ngrok-free.app',
    
    // Permissions Strava demandées
    STRAVA_SCOPES: 'read_all,activity:read_all',
    
    // Debug
    DEBUG: true
};

// Fonction utilitaire pour générer l'URL d'autorisation Strava
function getStravaAuthUrl(state = 'friends_invite') {
    const params = new URLSearchParams({
        client_id: CONFIG.STRAVA_CLIENT_ID,
        response_type: 'code',
        redirect_uri: CONFIG.STRAVA_REDIRECT_URI,
        approval_prompt: 'force',
        scope: CONFIG.STRAVA_SCOPES,
        state: state
    });
    
    return `https://www.strava.com/oauth/authorize?${params.toString()}`;
}

// Fonction pour les appels API
async function apiCall(endpoint, options = {}) {
    const url = `${CONFIG.API_BASE_URL}${endpoint}`;
    const defaultOptions = {
        headers: { 'Content-Type': 'application/json' }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    if (CONFIG.DEBUG) {
        console.log(`API Call: ${options.method || 'GET'} ${url}`, finalOptions);
    }
    
    try {
        const response = await fetch(url, finalOptions);
        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API Call failed:', error);
        throw error;
    }
}

// Validation de la configuration
function validateConfig() {
    const errors = [];
    
    if (CONFIG.STRAVA_CLIENT_ID === 'VOTRE_CLIENT_ID_STRAVA') {
        errors.push('STRAVA_CLIENT_ID non configuré');
    }
    
    if (CONFIG.STRAVA_REDIRECT_URI.includes('VOTRE-PROJECT-ID')) {
        errors.push('STRAVA_REDIRECT_URI non configuré - Remplacez VOTRE-PROJECT-ID par votre vrai Project ID Firebase');
    }
    
    if (CONFIG.API_BASE_URL.includes('VOTRE-NGROK-URL')) {
        errors.push('API_BASE_URL non configuré - Remplacez par votre URL ngrok actuelle');
    }
    
    return errors;
}

console.log('Configuration chargée:', CONFIG);