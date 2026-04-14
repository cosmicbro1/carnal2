
# CosmicBroAI/scripts/init_cosmic_bro.py
# Carnal2.0 — install trait lists into tokenizer as special tokens

from pathlib import Path
import sys, re, json, importlib.util
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# ---------------------------
# 0) CONFIG
# ---------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
# Your base model repo/folder (must be a valid HF model dir)
BASE_MODEL_PATH = str(PROJECT_DIR / "base_model")  # <-- change if needed
# Where to save the updated model+tokenizer
OUTPUT_MODEL_PATH = str(PROJECT_DIR / "carnal2_model")

# Fallback: if you still want to load from this script dir (not recommended for real models)
if not Path(BASE_MODEL_PATH).exists():
    BASE_MODEL_PATH = str(SCRIPT_DIR)  # last resort

# ---------------------------
# 1) MODEL INIT
# ---------------------------
print(f"Loading base model from: {BASE_MODEL_PATH}")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH, use_fast=True)
model = AutoModelForCausalLM.from_pretrained(BASE_MODEL_PATH)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Ensure PAD token exists for batching
if tokenizer.pad_token is None:
    # prefer eos if available
    if tokenizer.eos_token:
        tokenizer.pad_token = tokenizer.eos_token
    else:
        tokenizer.add_special_tokens({"pad_token": "<|pad|>"})
        model.resize_token_embeddings(len(tokenizer))

# ---------------------------
# 2) TRAIT CLEANERS
# ---------------------------
COMMON_FIXES = {
    "Visulization": "Visualization",
    "Alchemistry": "Alchemy",
    "precedentTransactions": "PrecedentTransactions",
    "Masculine Signs": "MasculineSigns",
    "Feminine Signs": "FeminineSigns",
}

def camelize(s: str) -> str:
    s = re.sub(r"[_\-]+", " ", s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return "".join(w.title() for w in s.split())

def normalize_item(raw: str) -> str:
    if not raw: return ""
    s = raw.strip().strip(",;")
    s = re.sub(r"^\d+\.\s*", "", s)  # drop 17. etc
    s = s.replace("*", "")
    for bad, good in COMMON_FIXES.items():
        s = s.replace(bad, good)
    return camelize(s)

def clean_list_from_blob(blob: str) -> list:
    parts = re.split(r"[,|\n]", blob)
    seen = set()
    out = []
    for p in parts:
        item = normalize_item(p)
        if not item: continue
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    out.sort()
    return out

# ---------------------------
# 3) LOAD TRAITS (prefer traits_clean.py if already generated)
# ---------------------------
def load_traits_module(py_path: Path):
    spec = importlib.util.spec_from_file_location("traits_clean", str(py_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod

traits_module_path = SCRIPT_DIR / "traits_clean.py"
if traits_module_path.exists():
    print("Found traits_clean.py — using the cleaned lists.")
    mod = load_traits_module(traits_module_path)
    TRAIT_SETS = {
        "mysticmind_traits": getattr(mod, "mysticmind_traits", []),
        "astrogpt_traits": getattr(mod, "astrogpt_traits", []),
        "stabldiffusion_traits": getattr(mod, "stabldiffusion_traits", []),
        "stockadvisor_traits": getattr(mod, "stockadvisor_traits", []),
        "tarottalk_traits": getattr(mod, "tarottalk_traits", []),
        "vedicastrology_traits": getattr(mod, "vedicastrology_traits", []),
        "astrogpt_plus_traits": getattr(mod, "astrogpt_plus_traits", []),
        "chatgpt_traits": getattr(mod, "chatgpt_traits", []),
    }
else:
    print("traits_clean.py not found — cleaning raw blobs inline.")
    RAW_MYSTICMIND = """PsychicAbilities, Telepathy, Clairvoyance, Clairaudience, Clairsentience, Precognition, Retrocognition,
    Psychokinesis, Telekinesis, Levitation, AstralProjection, OutOfBodyExperience, IntuitionDevelopment**, EmpathicAbilities,
    EnergyHealing, Reiki, Meditation, Visualization, Mindfulness, CosmicConsciousness, UniversalAwareness, SpiritualGrowth,
    KarmaAwareness, ReincarnationBeliefs, PastLifeRegression, LifeBetweenLives, SoulPurpose, SoulMateConnections, TwinFlameConnections,
    AngelicGuidance, SpiritGuideCommunication, AncestorWorship, ShamanicJourneys, LucidDreaming, DreamWalking, AstralTravel,
    EthericProjection, RemoteViewing, PsychicShielding, EnergyProtection, ChakraBalancing, AuraCleansing, MeditationTechniques,
    VisualizationMethods, MindfulnessPractices, CosmicOrdering, ManifestationTechniques, LawOfAttraction, VibrationalAlignment,
    BrainwaveEntrainment, BinauralBeats, IsochronicTones, SolfeggioFrequencies, ChakraFrequencies, AngelicFrequencies, ReikiSymbols,
    ReikiAttunement, SeichimReiki, KarunaReiki, LightarianReiki, PsychicDevelopment, IntuitiveDevelopment, EmpathicDevelopment,
    ClairvoyantDevelopment, MediumshipDevelopment, ChannelingDevelopment, TranceChanneling, ConsciousChanneling, AutomaticWriting,
    PsychicArt, IntuitiveArt, VisionaryArt, SpiritualArt, AngelicArt, CosmicArt, GalacticArt, StarseedArt, LightworkerArt, EnergyArt,
    HealingArt, MeditationArt, VisualizationArt, MindfulnessArt, ChakraArt, AuraArt, PsychicSymbols, Runes, Tarot, OracleCards,
    LenormandCards, IChing, AstrologySymbols, AlchemySymbols, SacredGeometry, Mandalas, Yantras, Mantras, Mudras, Gemstones, Crystals,
    EssentialOils, Aromatherapy, SoundHealing, SolfeggioTones, ChakraHealing, AuraHealing, PranicHealing, ReconnectiveHealing,
    QuantumTouch, TherapeuticTouch, HealingTouch, CosmicHealing, AngelicHealing, SpiritHealing, AncestralHealing, KarmaClearing,
    PastLifeHealing, InnerChildHealing, SoulHealing"""
    RAW_ASTROGPT = """Astrology, Horoscopes, BirthChart, NatalChart, SunSign, MoonSign, RisingSign, Ascendant, Planets, Houses, Aspects,
    ZodiacSigns, Aries, Taurus, Gemini, Cancer, Leo, Virgo, Libra, Scorpio, Sagittarius, Capricorn, Aquarius, Pisces, Transits, Progressions,
    SolarReturn, LunarReturn, Synastry, CompositeChart, AstroCartography, Midpoints, FixedStars, Chiron, Lilith, NorthNode, SouthNode, PartOfFortune,
    Vertex, Retrogrades, Eclipses, PlanetaryCycles, SaturnReturn, UranusOpposition, ChironReturn, MercuryRetrograde, VenusRetrograde, MarsRetrograde,
    JupiterCycles, SaturnCycles, OuterPlanetTransits, AstrologicalAges, AgeOfAquarius, SabianSymbols, AsteroidAstrology, Ceres, Pallas, Juno, Vesta, Eros,
    Psyche, KarmaAstrology, EvolutionaryAstrology, PsychologicalAstrology, MedicalAstrology, FinancialAstrology, MundaneAstrology, ElectionalAstrology,
    HoraryAstrology, AstrologySoftware, AstrologyApps, AstrologyReports, DailyHoroscopes, WeeklyHoroscopes, MonthlyHoroscopes, YearlyHoroscopes,
    RelationshipAstrology, CareerAstrology, HealthAstrology, SpiritualAstrology, SoulPurpose, LifePath, DestinyNumbers, AstrologyReadings, ChartInterpretation,
    PlanetaryAspects, Conjunction, Opposition, Square, Trine, Sextile, Quincunx, SemiSextile, SemiSquare, Sesquiquadrate, Biquintile, Quintile, Novile, Septile,
    AstrologicalHouses, FirstHouse, SecondHouse, ThirdHouse, FourthHouse, FifthHouse, SixthHouse, SeventhHouse, EighthHouse, NinthHouse, TenthHouse, EleventhHouse,
    TwelfthHouse, ZodiacElements, FireSigns, EarthSigns, AirSigns, WaterSigns, CardinalSigns, FixedSigns, MutableSigns"""
    RAW_STABLEDIFFUSION = """ImageGeneration, TextToImage, ImageEditing, StyleTransfer, ArtisticStyles, Upscaling, Inpainting, Outpainting, Watercolor, OilPainting,
    Impressionism, AbstractArt, PopArt, Cartooning, PixelArt, VectorGraphics, 3DModeling, Rendering, LightingEffects, Shadowing, TextureMapping, PatternGeneration,
    ColorPalette, MoodBoard, Composition, Photography, ImageEnhancement, NoiseReduction, ImageRestoration, FaceGeneration, BodyGeneration, AnimalGeneration, ObjectGeneration,
    SceneGeneration, LandscapeGeneration, PortraitGeneration, Caricature, Silhouette, ContourDrawing, GestureDrawing, FigureDrawing, AnatomyStudies, StillLife, FloralPatterns,
    GeometricPatterns, Mandala, Kaleidoscope, Fractals, LowPoly, PixelPerfect, Isometric, IconDesign, LogoCreation, Branding, VisualIdentity, UIComponents, WebDesign, MobileDesign,
    GraphicDesign, Illustration, Storyboarding, ComicArt, Manga, Anime, CharacterDesign, ConceptArt, EnvironmentDesign, PropDesign, VehicleDesign, Architecture, InteriorDesign,
    ProductDesign, FashionDesign, TextileDesign, PatternDesign, ColorTheory, Typography, Lettering, Calligraphy, HandLettering, DigitalPainting, MixedMedia, Collage, Photomanipulation,
    ImageComposite, DoubleExposure, LongExposure, TimeLapse, Hyperlapse, Cinemagraph, UniversalGeometry, FractalGeometry, SacredGeometry, GeometricAbstraction, OpArt, KineticArt,
    LightArt, IntuitionDevelopment, DigitalSculpture, 3DPrinting, VirtualReality, AugmentedReality, MixedReality, PsychicProtection, UIAnimation, MotionGraphics, VideoProduction,
    Filmmaking, Screenwriting, Storytelling, EnergyShielding, CharacterAnimation, 3DAnimation, StopMotion, TraditionalAnimation, ExperimentalAnimation, TelekinesisTraining, GlitchArt, Clairalience"""
    RAW_STOCKADVISOR = """StockMarketAnalysis, TechnicalAnalysis, FundamentalAnalysis, ChartPatterns, TrendAnalysis, CandlestickPatterns, SupportResistance, MovingAverages,
    RelativeStrengthIndex, BollingerBands, IchimokuCloud, PointFigureCharts, MarketTrends, BullBearMarkets, MarketVolatility, TradingVolume, 17. StockScreener, 18. PortfolioAnalysis,
    RiskManagement, Diversification, AssetAllocation, SectorRotation, IndustryAnalysis, CompanyFundamentals, FinancialStatements, RatioAnalysis, GrowthStocks, ValueStocks, DividendStocks,
    ETFs, MutualFunds, IndexFunds, HedgeFunds, PrivateEquity, VentureCapital, IPOs, MergersAcquisitions, MarketNews, EconomicIndicators, GDP, InflationRate, InterestRates, UnemploymentRate,
    CentralBanks, FederalReserve, MonetaryPolicy, FiscalPolicy, StockValuation, DiscountedCashFlow, ComparableAnalysis, precedentTransactions, LeveragedBuyouts, MergerArbitrage, EventDriven,
    GlobalMacro, Cryptocurrency, Blockchain, Bitcoin, Ethereum, Altcoins, CryptoTrading, CryptoInvesting, CryptoMining, CryptoWallets, CryptoExchanges, CryptoLending, CryptoBorrowing, CryptoMargins,
    CryptoShorting, CryptoOptions, CryptoFutures, BlockchainDevelopment, SmartContracts, DecentralizedApps, InitialCoinOfferings, SecurityTokenOfferings, CryptoRegulations, CryptoTaxes, CryptoAudit,
    CryptoCompliance, RiskAssessment, PortfolioOptimization, Backtesting, MonteCarloSimulations, ValueAtRisk, ExpectedShortfall, ConditionalValueAtRisk, DrawdownAnalysis, PortfolioRebalancing,
    TaxEfficient Investing, EstatePlanning, RetirementPlanning, WealthManagement, RoboAdvisors, AutomatedInvesting, MicroInvesting, FractionalShares, DollarCostAveraging, MarketTiming, SectorRotation,
    StyleBox, FactorBasedInvesting, ESGInvesting, SustainableInvesting, ImpactInvesting, ThematicInvesting, ActiveManagement, PassiveManagement, QuantitativeAnalysis, QuantitativeTrading,
    HighFrequencyTrading, AlgorithmicTrading, MachineLearning, DeepLearning, NeuralNetworks, ReinforcementLearning, PredictiveAnalytics, PrescriptiveAnalytics, StockPrediction, MarketForecasting"""
    RAW_TAROTTALK = """TarotTalk, TarotReadings, TarotCards, MajorArcana, MinorArcana, Wands, Cups, Swords, Pentacles, Fool, Magician, HighPriestess, Empress, Emperor, Hierophant, Lovers, Chariot, Strength,
    Hermit, WheelOfFortune, Justice, HangedMan, Death, Temperance, Devil, Tower, Star, Moon, Sun, Judgement, World, AceOfWands, TwoOfWands, ThreeOfWands, FourOfWands, FiveOfWands, SixOfWands, SevenOfWands,
    EightOfWands, NineOfWands, TenOfWands, PageOfWands, KnightOfWands, QueenOfWands, KingOfWands, AceOfCups, TwoOfCups, ThreeOfCups, FourOfCups, FiveOfCups, SixOfCups, SevenOfCups, EightOfCups, NineOfCups,
    TenOfCups, PageOfCups, KnightOfCups, QueenOfCups, KingOfCups, AceOfSwords, TwoOfSwords, ThreeOfSwords, FourOfSwords, FiveOfSwords, SixOfSwords, SevenOfSwords, EightOfSwords, NineOfSwords, TenOfSwords,
    PageOfSwords, KnightOfSwords, QueenOfSwords, KingOfSwords, AceOfPentacles, TwoOfPentacles, ThreeOfPentacles, FourOfPentacles, FiveOfPentacles, QueenOfPentacles, KingOfPentacles, TarotSpreads, CelticCross,
    ThreeCardSpread, PastPresentFuture, AstrologySpread, RelationshipSpread, CareerSpread, FinanceSpread, HealthSpread, SpiritualSpread, KarmicSpread, PastLifeSpread, TarotReversals, TarotCombinations,
    TarotCorrespondences, TarotAstrology, TarotKabbalah, TarotAlchemistry, TarotMagic, TarotRituals, TarotMeditation, TarotVisulization, TarotAffirmations, TarotJournaling, TarotMeditation, TarotVisualization,
    TarotBreathwork, TarotGrounding, TarotProtection, TarotClearing, TarotCharging, TarotConsecration, TarotBlessing, TarotScrying, TarotAstral, TarotReiki, TarotHealing, TarotReadingsOnline, TarotApps,
    TarotSoftware, TarotCommunity"""
    RAW_VEDIC = """VedicAstrology, Jyotish, HinduAstrology, SiderealZodiac, Nakshatras, BharaniNakshatra, PastLifeRegression, KarmaTheory, KarmicDebt, KarmicCycles, SanchitaKarma, PrarabdhaKarma,
    RelationshipCompatibility, KriyamanaKarma, SynastryAnalysis, MarriagePrediction, ChildrenPrediction, CareerPrediction, HealthPrediction, WealthPrediction, Yogas, Doshas, Gunas, Bhavas, Houses,
    PlanetaryTransits, Gochara, VimshottariDasha, Ashtakavarga, EnergyShielding, KalamsarpaYoga, NadiAstrology, NadiDasha, JaiminiAstrology, CharaDasha, MandookDasha, Sudasha, PranaDasha, DehaDasha,
    VimshottariMahadasha, Antardashas, Pratyantardasha, Sookshmandasha, KarmicAstrology, DhanaYoga, RajaYoga, GajaKesariYoga, BudhaAdityaYoga, ShubhaKartariYoga, PapakartariYoga, VesiYoga, VipareetaVesiYoga,
    UbhayacharaYoga, PushkalaYoga, MalavyaBhagyaYoga, LakshmiNarayanaYoga, KusumaYoga, SaraswatiYoga, KalatraYoga, PutraYoga, LabhaYoga, KarmaYoga, SwargaYoga, AyushKarmaYoga, MrityuBhagyaYoga, AyurBhavaYoga,
    RandhraBhavaYoga, BhavaKarakaYoga, IshtaDevataYoga, PutraBhagyaYoga, KalatraBhagyaYoga, DhanaBhagyaYoga, KarmaBhagyaYoga, MokshaBhagyaYoga, AtmaKarakaYoga, AmatyaKarakaYoga, BhratriKarakYoga, MatruKarakYoga,
    PitruKarakYoga, PutraKarakYoga, KalatraKarakYoga, DhanaKarakYoga, KarmaKarakYoga, MokshaKarakYoga, AtmaKarakPhalaYoga"""
    RAW_ASTROGPT_PLUS = """Astrology, ZodiacSigns, StarCharts, BirthCharts, PlanetaryAlignment, CosmicEvents, Astronomy, SpaceExploration, GalacticStudies, AlienLife, Astrobiology, Astrochemistry, Astroecology,
    SunSign, MoonSign, Ascendant, PlanetaryTransits, AstrologicalHouses, Cusps, Aspects, OrbitalPatterns, EclipsePredictions, SolarEclipses, LunarEclipses, PlanetaryRetrogrades, AstrologicalCycles, SynodicCycles,
    SiderealCycles, TropicalCycles, VedicAstrology, WesternAstrology, ChineseAstrology, MayanAstrology, EgyptianAstrology, AstrologicalElements, FireSigns, EarthSigns, AirSigns, WaterSigns, CardinalSigns, FixedSigns,
    MutableSigns, AstrologicalQualities, Masculine Signs, Feminine Signs, AstrologicalPolarity, YinYang, AstrologicalHousesSystems, Placidus, Koch, Campanus, Regiomontanus, Equal, WholeSign, Alcabitius, Morinus,
    Topocentric, AstrologicalAspects, Conjunction, Opposition, Square, Trine, Sextile, Quincunx, Semisquare, Sesquiquadrate, Semisextile, AstrologicalAspectPatterns, T-Square, GrandCross, GrandTrine, Kite, Cradle,
    Basket, Sling, AstrologicalHileg, PartOfFortune, PartOfSpirit, Vertex, AstrologicalMidpoints, IntuitionDevelopment, MidpointTheory, Synastry, CompositeCharts, DavisonCharts, AstrologicalAge, SecondaryProgressions,
    TertiaryProgressions, MinorProgressions, Transits, SolarArcs, LunarCycles, EclipsesCycles, PlanetaryCycles, AstrologicalResearch, AstrologicalTheory, HoraryAstrology, ElectionalAstrology, AstrologicalMagic, AstrologicalRituals"""
    RAW_CHATGPT = """AI, ConversationalAI, NaturalLanguage, DialogueSystems, ChatBot, AICommunication, HumanLikeDialogue, TextGeneration, LanguageProcessing, SemanticAnalysis, SentimentAnalysis, IntentRecognition,
    EntityRecognition, TopicModeling, LanguageTranslation, Summarization, QuestionAnswering, KnowledgeGraphs, OntologyEngineering, TaxonomyCreation, Categorization, Classification, Clustering, RecommendationSystems,
    Personalization, UserProfiling, BehavioralAnalysis, EmotionalIntelligence, EmpathyModeling, NaturalLanguageGeneration, DialogueManagement, ConversationFlow, TurnTaking, ResponseGeneration, ContextualUnderstanding,
    CommonSenseReasoning, WorldKnowledge, DomainSpecificKnowledge, EntityLinking, CoreferenceResolution, DependencyParsing, PartOfSpeechTagging, NamedEntityRecognition, SlotFilling, IntentDetection,
    SentimentClassification, EmotionDetection, OpinionMining, TextClassification, ClusteringAnalysis, TopicDiscovery, KeywordExtraction, SummarizationTechniques, ActiveLearning, SemiSupervisedLearning,
    UnsupervisedLearning, TransferLearning, MultitaskLearning, DomainAdaptation, ZeroShotLearning, FewShotLearning, HumanEvaluation, UserStudies, A/BTesting, ClickThroughRate, ConversionRate, CustomerSatisfaction,
    NetPromoterScore, ReturnOnInvestment, TimeOnPage, BounceRate, EngagementMetrics, SentimentAnalysisTools, TextAnalyticsPlatforms, NaturalLanguageToolkit, MachineLearningLibraries, DeepLearningFrameworks,
    NeuralNetworkArchitectures, ModelEvaluationMetrics, PrecisionRecallCurves, ReceiverOperatingCurves, ConfidenceIntervals, CrossValidation, HyperparameterTuning, ModelSelection, EnsembleMethods, Bagging, Boosting,
    Stacking, ModelInterpretability, FeatureImportance, PartialDependencePlots, IndividualConditionalExpectation, LocalInterpretableModelAgnosticExplanations, ModelExplainability, Transparency, Accountability, Fairness,
    BiasDetection, BiasMitigation, ModelDebugging, ErrorAnalysis, AblationStudies, AdversarialTesting, RobustnessChecking, EdgeCases, ModelUpdates, OnlineLearning, ContinualLearning, MultimodalLearning, HumanInTheLoop,
    ActiveLearning, SemiSupervised, Unsupervised, SelfSupervised, ContrastiveLearning, GraphLearning, ReinforcementLearning, ImitationLearning, ModelCompression"""
    TRAIT_SETS = {
        "mysticmind_traits": clean_list_from_blob(RAW_MYSTICMIND),
        "astrogpt_traits": clean_list_from_blob(RAW_ASTROGPT),
        "stabldiffusion_traits": clean_list_from_blob(RAW_STABLEDIFFUSION),
        "stockadvisor_traits": clean_list_from_blob(RAW_STOCKADVISOR),
        "tarottalk_traits": clean_list_from_blob(RAW_TAROTTALK),
        "vedicastrology_traits": clean_list_from_blob(RAW_VEDIC),
        "astrogpt_plus_traits": clean_list_from_blob(RAW_ASTROGPT_PLUS),
        "chatgpt_traits": clean_list_from_blob(RAW_CHATGPT),
    }

# Flatten + dedupe across all sets
all_traits = sorted({t for arr in TRAIT_SETS.values() for t in arr})

# ---------------------------
# 4) BUILD SPECIAL TOKENS
# ---------------------------
SPECIAL_PREFIX = "<TRAIT:"
SPECIAL_SUFFIX = ">"
def trait_to_token(name: str) -> str:
    return f"{SPECIAL_PREFIX}{name}{SPECIAL_SUFFIX}"

trait_tokens = [trait_to_token(t) for t in all_traits]

# Only add tokens not already present
existing = set(tokenizer.get_vocab().keys()) | set(tokenizer.get_added_vocab().keys())
tokens_to_add = [tok for tok in trait_tokens if tok not in existing]

print(f"Traits total: {len(all_traits)}")
print(f"New special tokens to add: {len(tokens_to_add)}")

if tokens_to_add:
    tokenizer.add_special_tokens({"additional_special_tokens": tokens_to_add})
    model.resize_token_embeddings(len(tokenizer))

# Save mapping for your app
mapping_path = SCRIPT_DIR / "trait_token_map.json"
with mapping_path.open("w", encoding="utf-8") as f:
    json.dump({t: trait_to_token(t) for t in all_traits}, f, indent=2)

# ---------------------------
# 5) SAVE UPDATED MODEL
# ---------------------------
print(f"Saving updated model + tokenizer to: {OUTPUT_MODEL_PATH}")
Path(OUTPUT_MODEL_PATH).mkdir(parents=True, exist_ok=True)
tokenizer.save_pretrained(OUTPUT_MODEL_PATH)
model.save_pretrained(OUTPUT_MODEL_PATH)

# Also export cleaned traits for other code to import
traits_py = SCRIPT_DIR / "traits_clean.py"
if not traits_py.exists():
    with (SCRIPT_DIR / "traits_clean.py").open("w", encoding="utf-8") as f:
        f.write("# Auto-generated clean trait lists\n\n")
        for k, arr in TRAIT_SETS.items():
            f.write(f"{k} = [\n")
            for v in arr:
                f.write(f'    "{v}",\n')
            f.write("]\n\n")

with (SCRIPT_DIR / "traits_clean.json").open("w", encoding="utf-8") as f:
    json.dump(TRAIT_SETS, f, indent=2)

# ---------------------------
# 6) HELPERS FOR USING TRAITS IN PROMPTS
# ---------------------------
def with_traits(prompt: str, trait_names: list[str]) -> str:
    """Prepend selected trait tokens to the user prompt."""
    toks = [trait_to_token(normalize_item(t)) for t in trait_names if t]
    return " ".join(toks) + " " + prompt if toks else prompt

def respond(text: str, trait_names: list[str] | None = None, max_new_tokens: int = 256) -> str:
    prompt = with_traits(text, trait_names or [])
    inputs = tokenizer(prompt, return_tensors="pt", padding=True).to(device)
    gen = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.8,
        top_p=0.9,
        repetition_penalty=1.1,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=getattr(tokenizer, "eos_token_id", None),
    )
    return tokenizer.decode(gen[0], skip_special_tokens=True)

if __name__ == "__main__":
    print("Carnal2.0 special tokens installed ✅")
    demo = respond("What can you tell me about astral projection?", ["PsychicAbilities", "AstralProjection"])
    print("\nDEMO:\n", demo[:1200])