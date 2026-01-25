// Simple i18n implementation for TrackRecord
// Base language is English, with translations available for other languages

export type Language = 'en' | 'es' | 'de' | 'fr' | 'ja' | 'zh' | 'he' | 'ar' | 'pt' | 'ru' | 'ko' | 'hi'

export const LANGUAGES: { code: Language; name: string; flag: string }[] = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'ja', name: '日本語', flag: '🇯🇵' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
  { code: 'he', name: 'עברית', flag: '🇮🇱' },
  { code: 'ar', name: 'العربية', flag: '🇸🇦' },
  { code: 'pt', name: 'Português', flag: '🇧🇷' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
  { code: 'ko', name: '한국어', flag: '🇰🇷' },
  { code: 'hi', name: 'हिन्दी', flag: '🇮🇳' },
]

// Translations dictionary
const translations: Record<Language, Record<string, string>> = {
  en: {
    // Navigation
    'nav.home': 'Home',
    'nav.predictions': 'Predictions',
    'nav.leaderboard': 'Leaderboard',
    'nav.submit': 'Submit',
    'nav.compete': 'Compete',
    'nav.resolve': 'Resolve',
    'nav.admin': 'Admin',
    
    // Hero
    'hero.title': 'Public Accountability for',
    'hero.titleHighlight': 'Public Predictions.',
    'hero.tagline': "Everyone's got an opinion. We keep score.",
    
    // Categories
    'category.all': 'All',
    'category.politics': 'Politics',
    'category.economy': 'Economy',
    'category.markets': 'Markets',
    'category.crypto': 'Crypto',
    'category.tech': 'Tech',
    'category.sports': 'Sports',
    'category.entertainment': 'Entertainment',
    'category.religion': 'Religion',
    'category.science': 'Science',
    'category.health': 'Health',
    'category.climate': 'Climate',
    'category.geopolitics': 'Geopolitics',
    
    // Regions
    'region.global': 'Global',
    'region.us': 'United States',
    'region.uk': 'United Kingdom',
    'region.eu': 'European Union',
    'region.china': 'China',
    'region.japan': 'Japan',
    'region.india': 'India',
    'region.israel': 'Israel',
    'region.russia': 'Russia',
    'region.brazil': 'Brazil',
    'region.latam': 'Latin America',
    'region.middleeast': 'Middle East',
    'region.africa': 'Africa',
    
    // Predictions
    'prediction.open': 'Open',
    'prediction.resolved': 'Resolved',
    'prediction.correct': 'Correct',
    'prediction.wrong': 'Wrong',
    'prediction.resolves': 'Resolves',
    
    // Actions
    'action.submit': 'Submit',
    'action.vote': 'Vote',
    'action.viewAll': 'View All',
    'action.learnMore': 'Learn More',
  },
  
  es: {
    'nav.home': 'Inicio',
    'nav.predictions': 'Predicciones',
    'nav.leaderboard': 'Clasificación',
    'nav.submit': 'Enviar',
    'nav.compete': 'Competir',
    'nav.resolve': 'Resolver',
    'nav.admin': 'Admin',
    'hero.title': 'Responsabilidad Pública para',
    'hero.titleHighlight': 'Predicciones Públicas.',
    'hero.tagline': 'Todos tienen una opinión. Nosotros llevamos la cuenta.',
    'category.all': 'Todo',
    'category.politics': 'Política',
    'category.economy': 'Economía',
    'category.markets': 'Mercados',
    'category.sports': 'Deportes',
    'prediction.open': 'Abierto',
    'prediction.resolved': 'Resuelto',
    'prediction.correct': 'Correcto',
    'prediction.wrong': 'Incorrecto',
    'action.submit': 'Enviar',
    'action.viewAll': 'Ver Todo',
  },
  
  de: {
    'nav.home': 'Startseite',
    'nav.predictions': 'Vorhersagen',
    'nav.leaderboard': 'Rangliste',
    'hero.title': 'Öffentliche Rechenschaft für',
    'hero.titleHighlight': 'Öffentliche Vorhersagen.',
    'hero.tagline': 'Jeder hat eine Meinung. Wir zählen die Punkte.',
    'category.all': 'Alle',
    'category.politics': 'Politik',
    'category.economy': 'Wirtschaft',
    'category.sports': 'Sport',
  },
  
  fr: {
    'nav.home': 'Accueil',
    'nav.predictions': 'Prédictions',
    'nav.leaderboard': 'Classement',
    'hero.title': 'Responsabilité Publique pour les',
    'hero.titleHighlight': 'Prédictions Publiques.',
    'hero.tagline': 'Tout le monde a un avis. Nous tenons les comptes.',
    'category.all': 'Tout',
    'category.politics': 'Politique',
    'category.economy': 'Économie',
    'category.sports': 'Sports',
  },
  
  ja: {
    'nav.home': 'ホーム',
    'nav.predictions': '予測',
    'nav.leaderboard': 'ランキング',
    'hero.title': '公的な説明責任のための',
    'hero.titleHighlight': '公的な予測。',
    'hero.tagline': '誰もが意見を持っています。私たちはスコアを記録します。',
    'category.all': 'すべて',
    'category.politics': '政治',
    'category.economy': '経済',
    'category.sports': 'スポーツ',
    'region.japan': '日本',
  },
  
  zh: {
    'nav.home': '首页',
    'nav.predictions': '预测',
    'nav.leaderboard': '排行榜',
    'hero.title': '公开预测的',
    'hero.titleHighlight': '公众问责。',
    'hero.tagline': '每个人都有观点。我们来计分。',
    'category.all': '全部',
    'category.politics': '政治',
    'category.economy': '经济',
    'category.sports': '体育',
    'region.china': '中国',
  },
  
  he: {
    'nav.home': 'בית',
    'nav.predictions': 'תחזיות',
    'nav.leaderboard': 'טבלת דירוג',
    'hero.title': 'אחריות ציבורית עבור',
    'hero.titleHighlight': 'תחזיות ציבוריות.',
    'hero.tagline': 'לכולם יש דעה. אנחנו סופרים נקודות.',
    'category.all': 'הכל',
    'category.politics': 'פוליטיקה',
    'category.economy': 'כלכלה',
    'category.sports': 'ספורט',
    'region.israel': 'ישראל',
  },
  
  ar: {
    'nav.home': 'الرئيسية',
    'nav.predictions': 'التوقعات',
    'nav.leaderboard': 'قائمة المتصدرين',
    'hero.title': 'المساءلة العامة عن',
    'hero.titleHighlight': 'التوقعات العامة.',
    'hero.tagline': 'كل شخص لديه رأي. نحن نحتفظ بالنتيجة.',
    'category.all': 'الكل',
    'category.politics': 'سياسة',
    'category.economy': 'اقتصاد',
    'category.sports': 'رياضة',
    'region.middleeast': 'الشرق الأوسط',
  },
  
  pt: {
    'nav.home': 'Início',
    'nav.predictions': 'Previsões',
    'nav.leaderboard': 'Classificação',
    'hero.title': 'Responsabilidade Pública para',
    'hero.titleHighlight': 'Previsões Públicas.',
    'hero.tagline': 'Todo mundo tem uma opinião. Nós mantemos a pontuação.',
    'category.all': 'Todos',
    'category.politics': 'Política',
    'category.economy': 'Economia',
    'category.sports': 'Esportes',
    'region.brazil': 'Brasil',
  },
  
  ru: {
    'nav.home': 'Главная',
    'nav.predictions': 'Прогнозы',
    'nav.leaderboard': 'Рейтинг',
    'hero.title': 'Публичная ответственность за',
    'hero.titleHighlight': 'Публичные прогнозы.',
    'hero.tagline': 'У каждого есть мнение. Мы ведём счёт.',
    'category.all': 'Все',
    'category.politics': 'Политика',
    'category.economy': 'Экономика',
    'category.sports': 'Спорт',
    'region.russia': 'Россия',
  },
  
  ko: {
    'nav.home': '홈',
    'nav.predictions': '예측',
    'nav.leaderboard': '순위표',
    'hero.title': '공개 예측에 대한',
    'hero.titleHighlight': '공적 책임.',
    'hero.tagline': '모든 사람이 의견을 가지고 있습니다. 우리는 점수를 기록합니다.',
    'category.all': '전체',
    'category.politics': '정치',
    'category.economy': '경제',
    'category.sports': '스포츠',
  },
  
  hi: {
    'nav.home': 'होम',
    'nav.predictions': 'भविष्यवाणियाँ',
    'nav.leaderboard': 'लीडरबोर्ड',
    'hero.title': 'सार्वजनिक भविष्यवाणियों के लिए',
    'hero.titleHighlight': 'सार्वजनिक जवाबदेही।',
    'hero.tagline': 'सभी की राय होती है। हम स्कोर रखते हैं।',
    'category.all': 'सभी',
    'category.politics': 'राजनीति',
    'category.economy': 'अर्थव्यवस्था',
    'category.sports': 'खेल',
    'region.india': 'भारत',
  },
}

// Get translation for a key in the specified language
export function t(key: string, lang: Language = 'en'): string {
  return translations[lang][key] || translations['en'][key] || key
}

// Get browser's preferred language
export function getBrowserLanguage(): Language {
  if (typeof window === 'undefined') return 'en'
  
  const browserLang = navigator.language.split('-')[0] as Language
  return LANGUAGES.some(l => l.code === browserLang) ? browserLang : 'en'
}

// Store language preference
export function setStoredLanguage(lang: Language): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('trackrecord-lang', lang)
  }
}

// Get stored language preference
export function getStoredLanguage(): Language {
  if (typeof window === 'undefined') return 'en'
  
  const stored = localStorage.getItem('trackrecord-lang') as Language
  return stored && LANGUAGES.some(l => l.code === stored) ? stored : getBrowserLanguage()
}
