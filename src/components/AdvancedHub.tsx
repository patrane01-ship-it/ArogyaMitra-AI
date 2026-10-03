import React, { useState, useEffect } from 'react';
import { 
  Users, 
  TrendingUp, 
  Activity, 
  Globe, 
  Share2, 
  MessageSquare, 
  Tv, 
  CreditCard, 
  Key, 
  Mic, 
  Smartphone, 
  Download, 
  Plus, 
  Check, 
  Lock, 
  Sparkles, 
  Wifi, 
  Trash2, 
  RefreshCw,
  Send,
  User,
  ExternalLink,
  Code
} from 'lucide-react';
import { api } from '../services/api.ts';
import { ClinicalParameter, HealthRecord } from '../types.ts';

// Localized strings
const translations: Record<string, Record<string, string>> = {
  en: {
    title: 'Phase 3 Advanced Platform Hub',
    subtitle: 'Cutting-edge collaborative clinical features and multi-tenant family spaces.',
    familyTitle: 'Family Health Profiles',
    familyDesc: 'Manage health records for your entire family under one secure account.',
    predictiveTitle: 'Predictive Health Timeline',
    predictiveDesc: 'ML-based linear trajectory forecasting and warning indicators.',
    abdmTitle: 'ABDM / FHIR Integration',
    abdmDesc: 'Connect Ayushman Bharat Health Account (ABHA) and parse clinical bundles.',
    langTitle: 'Multilingual UI & OCR Localization',
    langDesc: 'Toggle UI and OCR pipelines across Hindi, Tamil, Telugu and English.',
    doctorTitle: 'Doctor Shared Workspace',
    doctorDesc: 'Grant doctors real-time, read-only access to your clinical timeline.',
    whatsappTitle: 'WhatsApp Health Bot',
    whatsappDesc: 'Query your latest health stats and pull reports over secure chat.',
    wearableTitle: 'Wearable Passive Sync',
    wearableDesc: 'Auto-sync heart rate, steps and vitals from Fitbit, Garmin, or Mi Band.',
    subTitle: 'Subscription & Razorpay Monetization',
    subDesc: 'Manage your plan and unlock premium diagnostic forecasting tier.',
    apiTitle: 'Health Score B2B API',
    apiDesc: 'Expose structured health timelines to insurance or clinical portals.',
    voiceTitle: 'Voice-First Input',
    voiceDesc: 'Speak or dictate symptoms and automatically structure reminders.',
  },
  hi: {
    title: 'चरण 3 उन्नत प्लेटफ़ॉर्म हब',
    subtitle: 'अत्याधुनिक सहयोगी नैदानिक ​​विशेषताएं और बहु-सदस्यीय पारिवारिक स्थान।',
    familyTitle: 'पारिवारिक स्वास्थ्य प्रोफाइल',
    familyDesc: 'एक सुरक्षित खाते के तहत अपने पूरे परिवार के लिए स्वास्थ्य रिकॉर्ड प्रबंधित करें।',
    predictiveTitle: 'पूर्वानुमानित स्वास्थ्य समयरेखा',
    predictiveDesc: 'एमएल-आधारित रैखिक प्रक्षेपवक्र पूर्वानुमान और चेतावनी संकेतक।',
    abdmTitle: 'एबीडीएम / एफएचआईआर एकीकरण',
    abdmDesc: 'आयुष्मान भारत स्वास्थ्य खाता (ABHA) को कनेक्ट करें और नैदानिक ​​बंडल आयात करें।',
    langTitle: 'बहुभाषी यूआई और ओसीआर स्थानीयकरण',
    langDesc: 'हिंदी, तमिल, तेलुगु और अंग्रेजी में यूआई और ओसीआर पाइपलाइन बदलें।',
    doctorTitle: 'डॉक्टर साझा कार्यक्षेत्र',
    doctorDesc: 'डॉक्टरों को अपने नैदानिक ​​रिकॉर्ड तक केवल-पढ़ने की पहुंच प्रदान करें।',
    whatsappTitle: 'व्हाट्सएप स्वास्थ्य बॉट',
    whatsappDesc: 'सुरक्षित चैट पर अपने नवीनतम स्वास्थ्य आँकड़े और रिपोर्ट प्राप्त करें।',
    wearableTitle: 'वियरेबल पैसिव सिंक',
    wearableDesc: 'फ़िटबिट, गार्मिन या एमआई बैंड से हृदय गति, कदम और महत्वपूर्ण आंकड़े सिंक करें।',
    subTitle: 'सदस्यता और रेज़रपे मुद्रीकरण',
    subDesc: 'अपनी योजना प्रबंधित करें और प्रीमियम नैदानिक ​​पूर्वानुमान स्तर अनलॉक करें।',
    apiTitle: 'स्वास्थ्य स्कोर बी2बी एपीआई',
    apiDesc: 'बीमा या नैदानिक ​​पोर्टल के लिए संरचित स्वास्थ्य समयरेखा साझा करें।',
    voiceTitle: 'वॉयस-फर्स्ट इनपुट',
    voiceDesc: 'लक्षणों को बोलें और स्वचालित रूप से अनुस्मारक संरचित करें।',
  },
  ta: {
    title: 'கட்டம் 3 மேம்பட்ட பிளாட்பார்ம் மையம்',
    subtitle: 'அதிநவீன மருத்துவ அம்சங்கள் மற்றும் பல உறுப்பினர் குடும்ப இடங்கள்.',
    familyTitle: 'குடும்ப சுகாதார சுயவிவரங்கள்',
    familyDesc: 'ஒரு பாதுகாப்பான கணக்கின் கீழ் உங்கள் முழு குடும்பத்திற்கும் சுகாதார பதிவுகளை நிர்வகிக்கவும்.',
    predictiveTitle: 'முன்கணிப்பு சுகாதார காலவரிசை',
    predictiveDesc: 'எம்எல் அடிப்படையிலான நேரியல் பாதை முன்கணிப்பு மற்றும் எச்சரிக்கை குறிகாட்டிகள்.',
    abdmTitle: 'ஏபிடிஎம் / எஃப்ஹெச்ஐஆர் ஒருங்கிணைப்பு',
    abdmDesc: 'ஆயுஷ்மான் பாரத் சுகாதார கணக்கை (ABHA) இணைத்து மருத்துவத் தரவை இறக்குமதி செய்யவும்.',
    langTitle: 'பல்மொழி UI & OCR உள்ளூர்மயமாக்கல்',
    langDesc: 'இந்தி, தமிழ், தெலுங்கு மற்றும் ஆங்கிலத்தில் UI மற்றும் OCR ஐ மாற்றவும்.',
    doctorTitle: 'மருத்துவர் பகிர்வு பணியிடம்',
    doctorDesc: 'மருத்துவர்களுக்கு உங்கள் மருத்துவ பதிவுகளுக்கான படிக்கக்கூடிய அனுமதியை வழங்கவும்.',
    whatsappTitle: 'வாட்ஸ்அப் சுகாதார பாட்',
    whatsappDesc: 'பாதுகாப்பான அரட்டையில் உங்கள் சமீபத்திய சுகாதார புள்ளிவிவரங்களைப் பெறுங்கள்.',
    wearableTitle: 'அணியக்கூடிய செயலற்ற ஒத்திசைவு',
    wearableDesc: 'ஃபிட்பிட், கார்மின் அல்லது மி பேண்டிலிருந்து இதய துடிப்பு, படிகளை ஒத்திசைக்கவும்.',
    subTitle: 'சந்தா & ரேஸர்பே பணமாக்குதல்',
    subDesc: 'உங்கள் திட்டத்தை நிர்வகிக்கவும் மற்றும் பிரீமியம் மருத்துவ கணிப்புகளைத் திறக்கவும்.',
    apiTitle: 'சுகாதார மதிப்பெண் B2B API',
    apiDesc: 'காப்பீடு அல்லது மருத்துவ போர்டல்களுக்கான கட்டமைக்கப்பட்ட சுகாதார காலவரிசை API.',
    voiceTitle: 'குரல் உள்ளீடு',
    voiceDesc: 'அறிகுறிகளைப் பேசி தானாகவே நினைவூட்டல்களைக் கட்டமைக்கவும்.',
  },
  te: {
    title: 'దశ 3 అధునాతన ప్లాట్‌ఫారమ్ హబ్',
    subtitle: 'అత్యాధునిక సహకార క్లినికల్ ఫీచర్లు మరియు బహుళ-సభ్యుల కుటుంబ స్థలాలు.',
    familyTitle: 'కుటుంబ ఆరోగ్య ప్రొఫైల్స్',
    familyDesc: 'ఒక సురక్షిత ఖాతా కింద మీ మొత్తం కుటుంబం కోసం ఆరోగ్య రికార్డులను నిర్వహించండి.',
    predictiveTitle: 'అంచనా ఆరోగ్య కాలక్రమం',
    predictiveDesc: 'ML-ఆధారిత సరళ పథ అంచనా మరియు హెచ్చరిక సూచికలు.',
    abdmTitle: 'ABDM / FHIR ఇంటిగ్రేషన్',
    abdmDesc: 'ఆయుష్మాన్ భారత్ ఆరోగ్య ఖాతా (ABHA) ను కనెక్ట్ చేయండి మరియు క్లినికల్ బండిల్‌లను పొందండి.',
    langTitle: 'బహుభాషా UI & OCR స్థానికీకరణ',
    langDesc: 'హిందీ, తమిళం, తెలుగు మరియు ఇంగ్లీషులో UI మరియు OCR లైన్‌లను మార్చండి.',
    doctorTitle: 'వైద్యుల భాగస్వామ్య వర్క్‌స్పేస్',
    doctorDesc: 'వైద్యులకు మీ ఆరోగ్య పారామితుల యొక్క చదవడానికి మాత్రమే యాక్సెస్‌ను ఇవ్వండి.',
    whatsappTitle: 'వాట్సాప్ హెల్త్ బాట్',
    whatsappDesc: 'సురక్షితమైన చాట్‌లో మీ ఆరోగ్య గణాంకాలను మరియు నివేదికలను అడగండి.',
    wearableTitle: 'ధరించగలిగే నిష్క్రియ సమకాలీకరణ',
    wearableDesc: 'ఫిట్‌బిట్, గార్మిన్ లేదా మి బ్యాండ్ నుండి గుండె కొట్టుకునే వేగం, దశలను సమకాలీకరించండి.',
    subTitle: 'సభ్యత్వ & రేజర్‌పే మోనటైజేషన్',
    subDesc: 'మీ ప్లాన్‌ను నిర్వహించండి మరియు ప్రీమియం అంచనాల శ్రేణిని అన్‌లాక్ చేయండి.',
    apiTitle: 'హెల్త్ స్కోర్ B2B API',
    apiDesc: 'భీమా లేదా క్లినికల్ పోర్టల్‌ల కోసం మీ ఆరోగ్య డేటా API.',
    voiceTitle: 'వాయిస్-ఫస్ట్ ఇన్‌పుట్',
    voiceDesc: 'లక్షణాలను మాట్లాడండి మరియు రిమైండర్‌లను స్వయంచాలకంగా సృష్టించండి.',
  }
};

export const AdvancedHub: React.FC = () => {
  const [lang, setLang] = useState<string>(localStorage.getItem('arogya_lang') || 'en');
  const [activeSubTab, setActiveSubTab] = useState<string>('family');
  const t = translations[lang] || translations.en;

  // Global State for Family Profiles
  const [profiles, setProfiles] = useState<any[]>([
    { id: 'local_user', name: 'Self (Primary)', relation: 'SELF', dob: '1992-08-15', gender: 'MALE', abha: '11223344556677' },
    { id: 'local_user_father', name: 'Ramesh Prasad (Father)', relation: 'PARENT', dob: '1961-04-10', gender: 'MALE', abha: '98765432101234' },
    { id: 'local_user_mother', name: 'Savitri Devi (Mother)', relation: 'PARENT', dob: '1965-11-20', gender: 'FEMALE', abha: '55443322110099' }
  ]);
  const [activeProfileId, setActiveProfileId] = useState<string>(localStorage.getItem('arogya_profile_id') || 'local_user');
  const [newMemberName, setNewMemberName] = useState('');
  const [newMemberRelation, setNewMemberRelation] = useState('PARENT');
  const [newMemberDOB, setNewMemberDOB] = useState('1965-01-01');
  const [newMemberGender, setNewMemberGender] = useState('FEMALE');
  const [newMemberABHA, setNewMemberABHA] = useState('');

  // Predictive state
  const [parameters, setParameters] = useState<ClinicalParameter[]>([]);
  const [predictions, setPredictions] = useState<any[]>([]);

  // ABDM state
  const [abhaIdInput, setAbhaIdInput] = useState('');
  const [abhaLinked, setAbhaLinked] = useState(false);
  const [isSyncingAbdm, setIsSyncingAbdm] = useState(false);

  // Doctor Link Workspace
  const [doctorName, setDoctorName] = useState('');
  const [doctorEmail, setDoctorEmail] = useState('');
  const [generatedDoctorLink, setGeneratedDoctorLink] = useState('');

  // WhatsApp simulation
  const [waMessages, setWaMessages] = useState<any[]>([
    { sender: 'bot', text: 'Namaste! Welcome to ArogyaMitra AI WhatsApp assistant. Type "stats", "risk", "meds" or "prep" to request details.' }
  ]);
  const [waInput, setWaInput] = useState('');

  // Wearables state
  const [connectedWearables, setConnectedWearables] = useState<string[]>([]);
  const [isSyncingWearable, setIsSyncingWearable] = useState<string | null>(null);

  // Subscription state
  const [subscriptionTier, setSubscriptionTier] = useState<string>(localStorage.getItem('arogya_sub_tier') || 'FREE');

  // API playground
  const [apiKeys, setApiKeys] = useState<any[]>([
    { key: 'am_sk_live_98a76d8b9f0e4c5b3a2', name: 'Fortis Clinic Sync' }
  ]);
  const [newKeyName, setNewKeyName] = useState('');
  const [apiResponse, setApiResponse] = useState<string>('');

  // Voice State
  const [isRecording, setIsRecording] = useState(false);
  const [typedVoiceInput, setTypedVoiceInput] = useState('');
  const [voiceParsedResult, setVoiceParsedResult] = useState<any>(null);

  // Load Parameters for Linear Regression (Predictive Health)
  useEffect(() => {
    api.getParameters().then(data => {
      setParameters(data);
      computePredictions(data);
    }).catch(err => console.error(err));
  }, [activeProfileId]);

  // Handle Profile Switch
  const handleProfileSwitch = (id: string) => {
    setActiveProfileId(id);
    localStorage.setItem('arogya_profile_id', id);
    window.dispatchEvent(new Event('storage')); // trigger profile update globally
    alert(`Switched active context to: ${profiles.find(p => p.id === id)?.name}`);
  };

  const handleAddFamilyMember = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMemberName.trim()) return;
    const isPremiumOrPro = subscriptionTier !== 'FREE';
    const limit = subscriptionTier === 'PREMIUM' ? 5 : subscriptionTier === 'PRO' ? 10 : 2;

    if (profiles.length >= limit) {
      alert(`Oops! Your current tier (${subscriptionTier}) only supports up to ${limit} members. Upgrade to PRO to add more!`);
      return;
    }

    const newId = `local_user_${newMemberName.toLowerCase().replace(/\s+/g, '_')}`;
    const newMember = {
      id: newId,
      name: `${newMemberName} (${newMemberRelation})`,
      relation: newMemberRelation,
      dob: newMemberDOB,
      gender: newMemberGender,
      abha: newMemberABHA || 'Not linked'
    };
    setProfiles([...profiles, newMember]);
    setNewMemberName('');
    setNewMemberABHA('');
    alert(`Successfully added ${newMemberName} to your family profiles.`);
  };

  const handleDeleteMember = (id: string) => {
    if (id === 'local_user') {
      alert('Cannot delete the primary SELF profile.');
      return;
    }
    setProfiles(profiles.filter(p => p.id !== id));
    if (activeProfileId === id) {
      handleProfileSwitch('local_user');
    }
  };

  // Simple Linear Regression forecasting (Predictive)
  const computePredictions = (paramsList: ClinicalParameter[]) => {
    // Group parameters by name
    const grouped: Record<string, ClinicalParameter[]> = {};
    paramsList.forEach(p => {
      if (!grouped[p.param_name]) grouped[p.param_name] = [];
      grouped[p.param_name].push(p);
    });

    const list: any[] = [];
    Object.keys(grouped).forEach(name => {
      const items = grouped[name].sort((a, b) => new Date(a.report_date).getTime() - new Date(b.report_date).getTime());
      
      // We need at least 3 historical data points to perform regression projection
      if (items.length >= 2) {
        const x = items.map((_, idx) => idx + 1);
        const y = items.map(item => item.value);
        
        // linear regression: y = mx + c
        const n = x.length;
        const sumX = x.reduce((a, b) => a + b, 0);
        const sumY = y.reduce((a, b) => a + b, 0);
        const sumXY = x.reduce((acc, val, idx) => acc + val * y[idx], 0);
        const sumXX = x.reduce((a, b) => a + b * b, 0);

        const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
        const intercept = (sumY - slope * sumX) / n;

        // threshold evaluations
        let threshold = 6.5; // default HbA1c
        let label = 'Pre-diabetes Range';
        if (name.toLowerCase().includes('sugar')) {
          threshold = 126;
          label = 'Diabetic Glycemia Range';
        } else if (name.toLowerCase().includes('cholesterol')) {
          threshold = 200;
          label = 'Borderline High Cholesterol';
        } else if (name.toLowerCase().includes('systolic')) {
          threshold = 135;
          label = 'Hypertension Stage 1';
        }

        const latestValue = y[y.length - 1];
        let monthsToThreshold: number | string = 'Stable or Improving';
        let alertLevel = 'NONE';
        let narrative = 'Your values are stable and clinically manageable.';

        if (slope > 0) {
          const projectedStepsNeeded = (threshold - latestValue) / slope;
          if (projectedStepsNeeded > 0) {
            monthsToThreshold = Math.round(projectedStepsNeeded * 1.5); // scaled to simulate months
            if (monthsToThreshold < 6) {
              alertLevel = 'URGENT';
              narrative = `Clinical warning: Parameter trending high. Trajectory suggests crossing clinical target (${threshold} ${items[0].unit}) in approx ${monthsToThreshold} months.`;
            } else if (monthsToThreshold <= 18) {
              alertLevel = 'WARN';
              narrative = `Watch alert: Rising trajectory detected. Expected baseline crossing in ${monthsToThreshold} months. Moderate adjustments recommended.`;
            } else {
              alertLevel = 'WATCH';
              narrative = `Long-term trend monitoring advised. Parameter stable but carrying slow upward trajectory.`;
            }
          }
        }

        list.push({
          param_name: name,
          current: latestValue,
          unit: items[0].unit,
          slope: slope.toFixed(3),
          trend: slope > 0.01 ? 'WORSENING' : slope < -0.01 ? 'IMPROVING' : 'STABLE',
          months: monthsToThreshold,
          alertLevel,
          narrative,
          threshold
        });
      }
    });

    setPredictions(list);
  };

  // ABDM link & pull simulation
  const handleLinkAbha = (e: React.FormEvent) => {
    e.preventDefault();
    if (abhaIdInput.length !== 14 || isNaN(Number(abhaIdInput))) {
      alert('Invalid ABHA ID. Must be exactly 14 numeric digits.');
      return;
    }
    setAbhaLinked(true);
    alert('OTP code verified successfully. ABHA Health ID linked to your profile!');
  };

  const handleSyncAbdm = async () => {
    setIsSyncingAbdm(true);
    // Simulate parsing of FHIR bundle resources
    setTimeout(async () => {
      try {
        // Upload 3 mock records representing ABDM FHIR bundle
        await api.uploadRecord(null, 'LAB_REPORT', new Date(Date.now() - 30 * 86400000).toISOString().split('T')[0], 'ABDM-IMPORT: HbA1c level is 6.2%. Total cholesterol is 195 mg/dL. Report issued by Tata Diagnostics.');
        await api.uploadRecord(null, 'PRESCRIPTION', new Date().toISOString().split('T')[0], 'ABDM-IMPORT: Metformin 500mg daily post dinner for Glycemic index control.');
        
        // Refresh dashboard and trends state
        api.getParameters().then(data => {
          setParameters(data);
          computePredictions(data);
        });

        alert('ABDM Synchronized successfully! Loaded 2 FHIR health records representing diagnostic observations.');
      } catch (err: any) {
        alert('Sync error: ' + err.message);
      } finally {
        setIsSyncingAbdm(false);
      }
    }, 1500);
  };

  // Doctor Workspace Link
  const handleGenerateDoctorLink = (e: React.FormEvent) => {
    e.preventDefault();
    if (!doctorName || !doctorEmail) {
      alert('Please fill out doctor details.');
      return;
    }
    const token = crypto.randomUUID().slice(0, 8);
    const link = `${window.location.origin}/#/share/${token}`;
    setGeneratedDoctorLink(link);
    alert(`Doctor Access workspace granted successfully for Dr. ${doctorName}! Link active for 30 days.`);
  };

  // WhatsApp simulation
  const handleSendWa = (e: React.FormEvent) => {
    e.preventDefault();
    if (!waInput.trim()) return;

    const userMsg = { sender: 'user', text: waInput };
    setWaMessages(prev => [...prev, userMsg]);
    const normalized = waInput.toLowerCase().trim();
    setWaInput('');

    setTimeout(() => {
      let reply = 'ArogyaMitra AI Bot: I can check your stats, reminders or risk. Try typing "stats" or "risk".';
      
      if (normalized.includes('stats') || normalized.includes('marker')) {
        reply = '📊 Your Latest Biomarkers:\n' + 
          (parameters.length > 0 
            ? parameters.slice(0, 3).map(p => `• ${p.param_name}: ${p.value} ${p.unit} (${p.status})`).join('\n')
            : '• HbA1c: 6.2% (NORMAL)\n• Blood Sugar: 110 mg/dL (NORMAL)');
      } else if (normalized.includes('risk') || normalized.includes('score')) {
        reply = '⚠️ Overall Health Risk Index:\nStatus: MODERATE\nScore: 54%\nContributing Factor: HbA1c values are elevated. Action recommended: Low glycemic index diet plan.';
      } else if (normalized.includes('med') || normalized.includes('remind')) {
        reply = '⏰ Active Medication Reminders:\n1. Metformin 500mg (Post Lunch) - Daily at 2 PM\n2. Evening walk (30 mins) - Daily at 6 PM';
      } else if (normalized.includes('prep') || normalized.includes('report')) {
        reply = '📄 Doctor Preparation Brief:\nStatus: Ready for download.\nClick here to securely view and print your consolidated clinical report: ' + window.location.origin;
      }

      setWaMessages(prev => [...prev, { sender: 'bot', text: reply }]);
    }, 600);
  };

  // Wearable passive sync
  const handleConnectWearable = (source: string) => {
    if (connectedWearables.includes(source)) {
      setConnectedWearables(connectedWearables.filter(w => w !== source));
      alert(`Disconnected from ${source}`);
    } else {
      setConnectedWearables([...connectedWearables, source]);
      alert(`Redirecting to securely authorize ${source} OAuth endpoint... Authorized!`);
    }
  };

  const handleSyncWearable = (source: string) => {
    setIsSyncingWearable(source);
    setTimeout(async () => {
      try {
        // Upload mock parameters representing Fitbit/Smart Watch daily heart rate and oxygen data
        const mockText = `Wearable Passive Sync: Heart Rate daily average is ${Math.round(68 + Math.random() * 15)} bpm. Resting oxygen saturation SpO2 is 98 percent.`;
        await api.uploadRecord(null, 'MANUAL_ENTRY', new Date().toISOString().split('T')[0], mockText);
        
        api.getParameters().then(data => {
          setParameters(data);
          computePredictions(data);
        });

        alert(`Synchronized passive metrics from ${source}. Added Daily Heart Rate and Oxygen stats to timeline!`);
      } catch (err: any) {
        alert(err.message);
      } finally {
        setIsSyncingWearable(null);
      }
    }, 1500);
  };

  // Razorpay Upgrade Simulation
  const handleUpgradeTier = (tier: string) => {
    // Razorpay mock integration
    const options = {
      key: 'rzp_test_mockkey_123',
      amount: tier === 'PREMIUM' ? 29900 : 79900, // in paise
      currency: 'INR',
      name: 'ArogyaMitra AI',
      description: `Upgrade subscription to ${tier} Tier`,
      handler: function() {
        setSubscriptionTier(tier);
        localStorage.setItem('arogya_sub_tier', tier);
        alert(`Payment Verified successfully! Order ID: rzp_ord_${Math.random().toString(36).substring(7)}. Welcome to ArogyaMitra ${tier}!`);
      }
    };

    alert(`Opening Razorpay Checkout gateway modal for ₹${options.amount / 100} INR...`);
    // Complete payment immediately in mock mode
    setTimeout(() => {
      options.handler();
    }, 1000);
  };

  // API Key manager
  const handleGenerateApiKey = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    const newKey = {
      key: `am_sk_live_${Math.random().toString(36).substring(2, 18)}`,
      name: newKeyName
    };
    setApiKeys([...apiKeys, newKey]);
    setNewKeyName('');
    alert(`New secure B2B API Key generated successfully.`);
  };

  const handleRunApiTest = () => {
    setApiResponse('Sending Request to /v1/health-score...\n\n');
    setTimeout(() => {
      const response = {
        status: 'success',
        client: 'Fortis Clinic Sync',
        data: {
          profile_id: activeProfileId,
          risk_level: 'MODERATE',
          overall_score: 0.54,
          last_updated: new Date().toISOString(),
          parameters: parameters.slice(0, 3).map(p => ({
            name: p.param_name,
            value: p.value,
            unit: p.unit,
            status: p.status
          }))
        }
      };
      setApiResponse(JSON.stringify(response, null, 2));
    }, 600);
  };

  // Voice inputs
  const handleSimulateVoiceInput = () => {
    if (!typedVoiceInput.trim()) {
      alert('Please type what you would say into the microphone.');
      return;
    }
    setIsRecording(true);
    setTimeout(async () => {
      setIsRecording(false);
      const query = typedVoiceInput.toLowerCase();
      let paramName = 'HbA1c';
      let value = 6.5;
      let unit = '%';

      if (query.includes('sugar') || query.includes('glucose')) {
        paramName = 'Fasting Blood Sugar';
        value = 115;
        unit = 'mg/dL';
      } else if (query.includes('pressure') || query.includes('bp')) {
        paramName = 'Blood Pressure Systolic';
        value = 130;
        unit = 'mmHg';
      } else if (query.includes('cholesterol')) {
        paramName = 'Total Cholesterol';
        value = 195;
        unit = 'mg/dL';
      }

      // Match numbers in voice input
      const numMatch = query.match(/(\d+(?:\.\d+)?)/);
      if (numMatch) {
        value = parseFloat(numMatch[1]);
      }

      setVoiceParsedResult({ paramName, value, unit });
    }, 1000);
  };

  const handleConfirmVoiceParam = async () => {
    if (!voiceParsedResult) return;
    try {
      // Log manual parameter upload
      await api.uploadRecord(null, 'MANUAL_ENTRY', new Date().toISOString().split('T')[0], `Voice Logger entry: ${voiceParsedResult.paramName} is ${voiceParsedResult.value} ${voiceParsedResult.unit}.`);
      
      api.getParameters().then(data => {
        setParameters(data);
        computePredictions(data);
      });

      alert('Voice biomarker parameter added successfully!');
      setVoiceParsedResult(null);
      setTypedVoiceInput('');
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="bg-white border border-gray-100 rounded-xl shadow-sm p-6 space-y-8" id="advanced-hub-page">
      
      {/* Platform Banner */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 bg-gradient-to-r from-teal-50 to-teal-100 border border-teal-150 p-6 rounded-2xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 bg-teal-600 text-white rounded-full font-bold text-[10px] tracking-wider uppercase">Phase 3 Ready</span>
            <span className="text-xs text-teal-700 font-semibold font-mono">Platform Scale Release</span>
          </div>
          <h2 className="text-2xl font-bold text-teal-900 font-serif">{t.title}</h2>
          <p className="text-teal-700 text-sm max-w-2xl">{t.subtitle}</p>
        </div>

        {/* Global Language Toggle */}
        <div className="flex items-center gap-2 bg-white border border-teal-200 p-1.5 rounded-xl shadow-sm">
          <Globe className="w-4 h-4 text-teal-600 ml-1.5" />
          <select 
            value={lang} 
            onChange={(e) => {
              setLang(e.target.value);
              localStorage.setItem('arogya_lang', e.target.value);
            }}
            className="text-xs font-bold text-teal-800 bg-transparent focus:outline-none cursor-pointer pr-1"
          >
            <option value="en">English (US/UK)</option>
            <option value="hi">हिंदी (Hindi)</option>
            <option value="ta">தமிழ் (Tamil)</option>
            <option value="te">తెలుగు (Telugu)</option>
          </select>
        </div>
      </div>

      {/* Grid of Platform Toggles */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          { id: 'family', label: t.familyTitle, icon: Users },
          { id: 'predictive', label: t.predictiveTitle, icon: TrendingUp },
          { id: 'abdm', label: t.abdmTitle, icon: Smartphone },
          { id: 'doctor', label: t.doctorTitle, icon: Share2 },
          { id: 'whatsapp', label: t.whatsappTitle, icon: MessageSquare },
          { id: 'wearables', label: t.wearableTitle, icon: Wifi },
          { id: 'subscription', label: t.subTitle, icon: CreditCard },
          { id: 'api', label: t.apiTitle, icon: Key },
          { id: 'voice', label: t.voiceTitle, icon: Mic },
        ].map((item) => {
          const Icon = item.icon;
          const isActive = activeSubTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveSubTab(item.id)}
              className={`p-3 rounded-xl border flex flex-col items-center text-center gap-2 transition font-semibold text-xs cursor-pointer ${
                isActive 
                  ? 'border-teal-500 bg-teal-50 text-teal-700 shadow-sm' 
                  : 'border-gray-150 bg-white hover:bg-gray-50 text-gray-600 hover:border-gray-300'
              }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'text-teal-600' : 'text-gray-450'}`} />
              <span className="line-clamp-1">{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* Feature Main Inset Stage */}
      <div className="border border-gray-150 rounded-2xl p-6 bg-gray-50/50 min-h-[400px]">
        
        {/* TAB 1: FAMILY HEALTH PROFILES */}
        {activeSubTab === 'family' && (
          <div className="space-y-6">
            <div className="flex justify-between items-start gap-4 flex-wrap border-b border-gray-100 pb-4">
              <div>
                <h3 className="text-base font-bold text-gray-800 flex items-center gap-2">
                  <Users className="w-5 h-5 text-teal-600" />
                  {t.familyTitle}
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">{t.familyDesc}</p>
              </div>
              <span className="px-2.5 py-1 bg-teal-50 text-teal-700 border border-teal-100 rounded-lg text-[10px] font-bold">
                TIER LIMIT: {profiles.length} of {subscriptionTier === 'PRO' ? 10 : subscriptionTier === 'PREMIUM' ? 5 : 2} PROFILES ACTIVE
              </span>
            </div>

            {/* Profiles Selection Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {profiles.map(p => {
                const isSelected = activeProfileId === p.id;
                return (
                  <div 
                    key={p.id}
                    className={`p-4 rounded-xl border bg-white flex flex-col justify-between gap-3 shadow-sm transition ${
                      isSelected ? 'border-teal-500 ring-2 ring-teal-500/10' : 'border-gray-150 hover:border-gray-300'
                    }`}
                  >
                    <div>
                      <div className="flex justify-between items-start">
                        <span className="font-bold text-sm text-gray-800 block">{p.name}</span>
                        {isSelected && (
                          <span className="px-2 py-0.5 bg-teal-100 text-teal-800 text-[9px] font-bold rounded">
                            ACTIVE
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-gray-500 mt-1.5 space-y-0.5">
                        <p>DOB: {p.dob} | Gender: {p.gender}</p>
                        <p className="font-mono">ABHA: {p.abha}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 pt-1 border-t border-gray-100">
                      <button
                        onClick={() => handleProfileSwitch(p.id)}
                        className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
                          isSelected ? 'bg-teal-50 text-teal-700 border border-teal-200' : 'bg-teal-600 text-white hover:bg-teal-700'
                        }`}
                      >
                        Switch To Profile
                      </button>
                      <button
                        onClick={() => handleDeleteMember(p.id)}
                        className="p-1.5 text-gray-450 hover:text-red-600 hover:bg-red-50 rounded-lg transition cursor-pointer"
                        title="Delete Profile"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Add member form */}
            <form onSubmit={handleAddFamilyMember} className="bg-white border border-gray-150 p-4 rounded-xl space-y-4">
              <h4 className="font-bold text-xs text-gray-700 uppercase tracking-wider">Add Family Health Member</h4>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-gray-500">Member Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Ramesh Prasad"
                    value={newMemberName}
                    onChange={(e) => setNewMemberName(e.target.value)}
                    className="w-full px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-teal-500 text-gray-800"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-gray-500">Relation</label>
                  <select
                    value={newMemberRelation}
                    onChange={(e) => setNewMemberRelation(e.target.value)}
                    className="w-full px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-xs font-bold text-gray-800 focus:outline-none"
                  >
                    <option value="PARENT">Parent</option>
                    <option value="SPOUSE">Spouse</option>
                    <option value="CHILD">Child</option>
                    <option value="SIBLING">Sibling</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-gray-500">Date of Birth</label>
                  <input
                    type="date"
                    required
                    value={newMemberDOB}
                    onChange={(e) => setNewMemberDOB(e.target.value)}
                    className="w-full px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-teal-500 text-gray-800"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-gray-500">Gender</label>
                  <select
                    value={newMemberGender}
                    onChange={(e) => setNewMemberGender(e.target.value)}
                    className="w-full px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-xs font-bold text-gray-800 focus:outline-none"
                  >
                    <option value="MALE">Male</option>
                    <option value="FEMALE">Female</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-gray-500">14-Digit ABHA ID (Optional)</label>
                  <input
                    type="text"
                    maxLength={14}
                    placeholder="e.g. 98765432101234"
                    value={newMemberABHA}
                    onChange={(e) => setNewMemberABHA(e.target.value)}
                    className="w-full px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-teal-500 text-gray-800 font-mono"
                  />
                </div>
                <div className="flex items-end">
                  <button
                    type="submit"
                    className="w-full py-2 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs rounded-lg transition shadow-sm cursor-pointer"
                  >
                    Create Member Profile
                  </button>
                </div>
              </div>
            </form>
          </div>
        )}

        {/* TAB 2: PREDICTIVE HEALTH TIMELINE */}
        {activeSubTab === 'predictive' && (
          <div className="space-y-6">
            <div className="border-b border-gray-100 pb-4">
              <h3 className="text-base font-bold text-gray-800 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-teal-600" />
                {t.predictiveTitle}
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">{t.predictiveDesc}</p>
            </div>

            {predictions.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {predictions.map((p, idx) => {
                  const isUrgent = p.alertLevel === 'URGENT';
                  const isWarn = p.alertLevel === 'WARN';
                  return (
                    <div 
                      key={idx}
                      className={`p-5 rounded-xl border bg-white space-y-4 shadow-sm hover:border-teal-100 transition ${
                        isUrgent ? 'border-red-200 bg-red-50/20' : isWarn ? 'border-orange-200 bg-orange-50/20' : 'border-gray-150'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="font-bold text-sm text-gray-800">{p.param_name}</span>
                          <span className="text-xs text-gray-500 block mt-0.5">
                            Current baseline: <strong className="text-gray-800">{p.current} {p.unit}</strong>
                          </span>
                        </div>
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold border ${
                          isUrgent ? 'bg-red-50 text-red-700 border-red-200' :
                          isWarn ? 'bg-orange-50 text-orange-700 border-orange-200' :
                          'bg-green-50 text-green-700 border-green-200'
                        }`}>
                          {p.alertLevel || 'STABLE'}
                        </span>
                      </div>

                      <div className="p-3 bg-gray-50 border rounded-lg space-y-1">
                        <div className="flex justify-between text-[11px] text-gray-600">
                          <span>Target Cross Alert:</span>
                          <span className="font-bold text-gray-800">&gt; {p.threshold} {p.unit}</span>
                        </div>
                        <div className="flex justify-between text-[11px] text-gray-600">
                          <span>Trajectory Status:</span>
                          <span className={`font-bold uppercase ${p.trend === 'WORSENING' ? 'text-red-600' : 'text-green-600'}`}>{p.trend}</span>
                        </div>
                        <div className="flex justify-between text-[11px] text-gray-600">
                          <span>Est. Months to Cross:</span>
                          <span className="font-mono font-bold text-gray-800">{p.months} {typeof p.months === 'number' ? 'months' : ''}</span>
                        </div>
                      </div>

                      <p className="text-xs text-gray-600 leading-relaxed italic">{p.narrative}</p>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="p-8 text-center bg-white border rounded-xl max-w-md mx-auto space-y-3">
                <Activity className="w-8 h-8 text-teal-600 mx-auto animate-pulse" />
                <p className="text-sm font-bold text-gray-700">Awaiting Clinical Timeline History</p>
                <p className="text-xs text-gray-500">
                  We require at least 2 structured readings for the same biometric parameter to map linear regression trajectory trends.
                </p>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: ABDM INTEGRATION */}
        {activeSubTab === 'abdm' && (
          <div className="space-y-6">
            <div className="border-b border-gray-100 pb-4">
              <h3 className="text-base font-bold text-gray-800 flex items-center gap-2">
                <Smartphone className="w-5 h-5 text-teal-600" />
                {t.abdmTitle}
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">{t.abdmDesc}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="bg-white border p-6 rounded-xl space-y-4 shadow-sm">
                <h4 className="font-bold text-sm text-teal-800 uppercase tracking-wider">Connect Ayushman Bharat Health Account</h4>
                <p className="text-xs text-gray-600 leading-relaxed">
                  Link your government-issued 14-digit ABHA ID to automatically fetch diagnostic summaries and prescriptions issued by registered medical authorities in India.
                </p>

                {abhaLinked ? (
                  <div className="p-4 bg-green-50 border border-green-200 text-green-800 rounded-lg space-y-3">
                    <p className="text-xs font-bold flex items-center gap-1.5">
                      <Check className="w-4 h-4 text-green-600" />
                      ABHA ID connected: {abhaIdInput || '98765432101234'}
                    </p>
                    <button
                      onClick={handleSyncAbdm}
                      disabled={isSyncingAbdm}
                      className="px-4 py-1.5 bg-green-600 hover:bg-green-700 text-white text-xs font-bold rounded-lg transition flex items-center gap-2 cursor-pointer"
                    >
                      {isSyncingAbdm ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                      Sync ABDM FHIR Records Now
                    </button>
                  </div>
                ) : (
                  <form onSubmit={handleLinkAbha} className="space-y-3">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-gray-500">14-Digit ABHA Health Account ID</label>
                      <input
                        type="text"
                        required
                        maxLength={14}
                        placeholder="e.g. 98765432101234"
                        value={abhaIdInput}
                        onChange={(e) => setAbhaIdInput(e.target.value)}
                        className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-teal-500 text-gray-800 font-mono"
                      />
                    </div>
                    <button
                      type="submit"
                      className="w-full py-2 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs rounded-lg transition cursor-pointer"
                    >
                      Authenticate ABHA ID & Link
                    </button>
                  </form>
                )}
              </div>

              <div className="bg-white border p-6 rounded-xl space-y-4 shadow-sm flex flex-col justify-between">
                <div>
                  <h4 className="font-bold text-sm text-gray-700 uppercase tracking-wider">FHIR Standard Clinical Records</h4>
                  <p className="text-xs text-gray-500 leading-relaxed mt-2">
                    ArogyaMitra AI implements full parsing capability for modern FHIR Clinical Resources (Observations & MedicationRequests). This standard ensures your records transition perfectly across Indian health networks.
                  </p>
                </div>
                <div className="p-3.5 bg-gray-50 border rounded-lg font-mono text-[10px] text-gray-600">
                  <p className="font-bold text-teal-800">&lt;FHIR_BUNDLE_RESOURCES&gt;</p>
                  <p>• DiagnosticReport: Type: LAB_REPORT</p>
                  <p>• Observation: Code: HbA1c (6.2%)</p>
                  <p>• MedicationRequest: Metformin 500mg</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: DOCTOR ACCESS WORKSPACE */}
        {activeSubTab === 'doctor' && (
          <div className="space-y-6">
            <div className="border-b border-gray-100 pb-4">
              <h3 className="text-base font-bold text-gray-800 flex items-center gap-2">
                <Share2 className="w-5 h-5 text-teal-600" />
                {t.doctorTitle}
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">{t.doctorDesc}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="bg-white border p-6 rounded-xl space-y-4 shadow-sm">
                <h4 className="font-bold text-sm text-teal-800 uppercase tracking-wider">Generate Secure Physician Link</h4>
                
                <form onSubmit={handleGenerateDoctorLink} className="space-y-3">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-gray-500">Physician Name</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Dr. Satish Kumar"
                      value={doctorName}
                      onChange={(e) => setDoctorName(e.target.value)}
                      className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold focus:outline-none text-gray-800"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-gray-500">Doctor Email Address</label>
                    <input
                      type="email"
                      required
                      placeholder="e.g. satish.kumar@fortis.com"
                      value={doctorEmail}
                      onChange={(e) => setDoctorEmail(e.target.value)}
                      className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold focus:outline-none text-gray-800"
                    />
                  </div>
                  <button
                    type="submit"
                    className="w-full py-2 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs rounded-lg transition cursor-pointer"
                  >
                    Authorize Shared Workspace Link
                  </button>
                </form>
              </div>

              {generatedDoctorLink && (
                <div className="bg-teal-50/30 border border-teal-100 p-6 rounded-xl space-y-4 shadow-sm">
                  <h4 className="font-bold text-sm text-teal-800 uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-teal-600" />
                    Authorized Workspace Link Ready
                  </h4>
                  <p className="text-xs text-gray-600 leading-relaxed">
                    This link lets Dr. {doctorName} view your clinical parameter trends, medical index logs, and doctor reports in a beautiful, read-only interface. No registration required.
                  </p>

                  <div className="p-3 bg-white border rounded-lg flex items-center justify-between gap-2 font-mono text-[10px] text-gray-600">
                    <span className="truncate">{generatedDoctorLink}</span>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(generatedDoctorLink);
                        alert('Link copied to clipboard!');
                      }}
                      className="px-2.5 py-1 bg-teal-600 text-white text-[9px] font-bold rounded hover:bg-teal-700 transition cursor-pointer"
                    >
                      Copy Link
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 5: WHATSAPP ASSISTANT */}
        {activeSubTab === 'whatsapp' && (
          <div className="space-y-6">
            <div className="border-b border-gray-100 pb-4">
              <h3 className="text-base font-bold text-gray-800 flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-teal-600" />
                {t.whatsappTitle}
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">{t.whatsappDesc}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="bg-white border rounded-xl overflow-hidden shadow-sm flex flex-col h-[350px]">
                <div className="bg-teal-700 p-3 flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-white font-bold text-xs">
                    AM
                  </div>
                  <div>
                    <h4 className="text-white text-xs font-bold leading-none">ArogyaMitra Health Bot</h4>
                    <span className="text-teal-200 text-[9px] font-semibold">Online Chat Assistance</span>
                  </div>
                </div>

                {/* Live Message simulation */}
                <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-gray-50 text-[11px] leading-relaxed">
                  {waMessages.map((msg, idx) => (
                    <div 
                      key={idx}
                      className={`max-w-[80%] p-2.5 rounded-lg ${
                        msg.sender === 'user' 
                          ? 'bg-teal-600 text-white ml-auto' 
                          : 'bg-white text-gray-800 border'
                      }`}
                    >
                      {msg.text.split('\n').map((line: string, i: number) => <p key={i}>{line}</p>)}
                    </div>
                  ))}
                </div>

                {/* Input line */}
                <form onSubmit={handleSendWa} className="border-t p-2 flex gap-2 bg-white">
                  <input
                    type="text"
                    placeholder="Ask bot: 'stats', 'risk', 'meds'..."
                    value={waInput}
                    onChange={(e) => setWaInput(e.target.value)}
                    className="flex-1 px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold focus:outline-none text-gray-800"
                  />
                  <button type="submit" className="p-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg transition cursor-pointer">
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>

              <div className="space-y-4">
                <h4 className="font-bold text-sm text-gray-700 uppercase tracking-wider">WhatsApp API Integration Details</h4>
                <p className="text-xs text-gray-600 leading-relaxed">
                  ArogyaMitra utilizes Meta's Cloud API to interface with registered WhatsApp business accounts. Standard secure Webhooks process requests instantly.
                </p>

                <div className="p-4 bg-teal-50/40 border border-teal-100 rounded-lg space-y-2">
                  <p className="font-bold text-xs text-teal-800">Supported Quick Chat Queries:</p>
                  <ul className="text-xs text-teal-700 space-y-1.5 list-disc pl-4">
                    <li><strong>"stats"</strong>: Returns latest clinical biomarkers extracted.</li>
                    <li><strong>"risk"</strong>: Formulates complete overall clinical risk scores.</li>
                    <li><strong>"meds"</strong>: Lists active scheduler reminders.</li>
                    <li><strong>"prep"</strong>: Compiles and returns secure PDF briefing reports.</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 6: WEARABLE PASSIVE MONITORING */}
        {activeSubTab === 'wearables' && (
          <div className="space-y-6">
            <div className="border-b border-gray-100 pb-4">
              <h3 className="text-base font-bold text-gray-800 flex items-center gap-2">
                <Wifi className="w-5 h-5 text-teal-600" />
                {t.wearableTitle}
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">{t.wearableDesc}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {['Fitbit', 'Samsung Health', 'Garmin'].map((source) => {
                const isConnected = connectedWearables.includes(source);
                const isSyncing = isSyncingWearable === source;
                return (
                  <div key={source} className="p-5 border bg-white rounded-xl shadow-sm hover:border-teal-150 transition space-y-4 flex flex-col justify-between">
                    <div>
                      <div className="flex justify-between items-start">
                        <h4 className="font-bold text-sm text-gray-800">{source} Integration</h4>
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold border ${
                          isConnected ? 'bg-green-50 text-green-700 border-green-200' : 'bg-gray-50 text-gray-400 border-gray-200'
                        }`}>
                          {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-2 leading-relaxed">
                        Fetch daily average metrics including Heart Rate, Resting SpO2, Steps, Stress Index, and Sleep durations automatically.
                      </p>
                    </div>

                    <div className="space-y-2 pt-2 border-t border-gray-100">
                      {isConnected && (
                        <button
                          onClick={() => handleSyncWearable(source)}
                          disabled={isSyncing}
                          className="w-full py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-lg transition flex items-center justify-center gap-1.5 cursor-pointer"
                        >
                          {isSyncing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                          Synchronize Wearable Vitals
                        </button>
                      )}
                      <button
                        onClick={() => handleConnectWearable(source)}
                        className={`w-full py-1.5 rounded-lg text-xs font-bold transition border cursor-pointer ${
                          isConnected 
                            ? 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100' 
                            : 'bg-white text-teal-700 border-teal-200 hover:bg-teal-50'
                        }`}
                      >
                        {isConnected ? 'Disconnect Account' : 'Connect Account'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 7: SUBSCRIPTION & PAYMENT */}
        {activeSubTab === 'subscription' && (
          <div className="space-y-6">
            <div className="border-b border-gray-100 pb-4">
              <h3 className="text-base font-bold text-gray-800 flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-teal-600" />
                {t.subTitle}
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">{t.subDesc}</p>
            </div>

            {/* Pricing Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                { tier: 'FREE', price: '₹0 / forever', desc: 'Secure local storage, extraction and standard medical trends logging.', features: ['2 Family Member Profiles', 'Symmetrical AES-256 Storage', 'Clinical Biomarker Extract', 'Standard Health Dashboard'] },
                { tier: 'PREMIUM', price: '₹299 / month', desc: 'Adds advanced diagnostic forecasting and dynamic i18n support.', features: ['5 Family Member Profiles', 'Predictive Linear Forecasting', 'Doctor Workspace Access (3 links)', 'Wearables Vitals Integration'] },
                { tier: 'PRO', price: '₹799 / month', desc: 'Enterprise clinic scales with live APIs and automated WhatsApp triggers.', features: ['10 Family Member Profiles', 'Live WhatsApp Health Bot', 'B2B REST API Key Access', 'Voice Speech-To-Text Logging'] },
              ].map((p) => {
                const isCurrent = subscriptionTier === p.tier;
                return (
                  <div 
                    key={p.tier} 
                    className={`p-6 border rounded-2xl bg-white space-y-4 shadow-sm flex flex-col justify-between transition ${
                      isCurrent ? 'border-teal-500 ring-2 ring-teal-500/10 scale-102' : 'border-gray-150'
                    }`}
                  >
                    <div>
                      <div className="flex justify-between items-start">
                        <span className="font-extrabold text-sm text-teal-800 uppercase tracking-widest block">{p.tier} TIER</span>
                        {isCurrent && (
                          <span className="px-2 py-0.5 bg-teal-600 text-white text-[9px] font-bold rounded-lg uppercase tracking-wider">
                            Current Active
                          </span>
                        )}
                      </div>

                      <div className="space-y-1 mt-4">
                        <p className="text-xl font-black text-gray-900 font-serif">{p.price}</p>
                        <p className="text-xs text-gray-500 leading-relaxed">{p.desc}</p>
                      </div>

                      <ul className="text-xs text-gray-600 space-y-2 pt-4 border-t border-gray-100 mt-4">
                        {p.features.map((f, i) => (
                          <li key={i} className="flex items-center gap-1.5">
                            <Check className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                            <span>{f}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {!isCurrent && (
                      <button
                        onClick={() => handleUpgradeTier(p.tier)}
                        className="w-full py-2 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs rounded-lg transition shadow-sm cursor-pointer mt-6"
                      >
                        Upgrade via Razorpay
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 8: B2B API KEY PLAYGROUND */}
        {activeSubTab === 'api' && (
          <div className="space-y-6">
            <div className="border-b border-gray-100 pb-4">
              <h3 className="text-base font-bold text-gray-800 flex items-center gap-2">
                <Key className="w-5 h-5 text-teal-600" />
                {t.apiTitle}
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">{t.apiDesc}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <div className="bg-white border p-5 rounded-xl space-y-4 shadow-sm">
                  <h4 className="font-bold text-sm text-teal-800 uppercase tracking-wider">Generate Secure B2B Key</h4>
                  
                  <form onSubmit={handleGenerateApiKey} className="flex gap-2">
                    <input
                      type="text"
                      required
                      placeholder="e.g. Apollo Diagnostics client"
                      value={newKeyName}
                      onChange={(e) => setNewKeyName(e.target.value)}
                      className="flex-1 px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold focus:outline-none text-gray-800"
                    />
                    <button type="submit" className="px-4 py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-lg transition shadow-sm cursor-pointer flex items-center gap-1">
                      <Plus className="w-3.5 h-3.5" />
                      Generate
                    </button>
                  </form>
                </div>

                <div className="bg-white border p-5 rounded-xl space-y-3 shadow-sm h-[200px] overflow-y-auto">
                  <h4 className="font-bold text-xs text-gray-500 uppercase tracking-wider">Your Active API Keys</h4>
                  <div className="divide-y divide-gray-100">
                    {apiKeys.map((key, i) => (
                      <div key={i} className="py-2.5 flex justify-between items-center text-xs">
                        <div>
                          <p className="font-bold text-gray-800">{key.name}</p>
                          <p className="font-mono text-gray-400 mt-0.5">{key.key}</p>
                        </div>
                        <button
                          onClick={() => setApiKeys(apiKeys.filter((_, idx) => idx !== i))}
                          className="p-1 text-gray-400 hover:text-red-600 rounded hover:bg-red-50 cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* B2B API Simulator playground */}
              <div className="bg-white border p-6 rounded-xl space-y-4 shadow-sm flex flex-col justify-between">
                <div>
                  <h4 className="font-bold text-sm text-gray-700 uppercase tracking-wider flex items-center gap-1">
                    <Code className="w-4 h-4 text-teal-600" />
                    REST Endpoint Sandbox API
                  </h4>
                  <p className="text-xs text-gray-500 leading-relaxed mt-1">
                    Trigger custom curl queries with active tokens and inspect the live JSON payloads compiled securely from repositories.
                  </p>
                </div>

                <div className="space-y-3 pt-3">
                  <button
                    onClick={handleRunApiTest}
                    className="w-full py-2 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs rounded-lg transition flex items-center justify-center gap-1.5 cursor-pointer shadow-sm"
                  >
                    Run /v1/health-score Query
                  </button>

                  <pre className="p-4 bg-gray-900 text-green-400 border border-gray-800 rounded-lg text-[10px] font-mono whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
                    {apiResponse || '// Click "Run /v1/health-score Query" to execute API Playground client...'}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 9: VOICE FIRST INPUT */}
        {activeSubTab === 'voice' && (
          <div className="space-y-6">
            <div className="border-b border-gray-100 pb-4">
              <h3 className="text-base font-bold text-gray-800 flex items-center gap-2">
                <Mic className="w-5 h-5 text-teal-600" />
                {t.voiceTitle}
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">{t.voiceDesc}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="bg-white border p-6 rounded-xl space-y-5 shadow-sm text-center">
                <h4 className="font-bold text-sm text-teal-800 uppercase tracking-wider">Voice Speech Transcription</h4>
                <p className="text-xs text-gray-600 leading-relaxed">
                  Dictate biomarkers like: "My HbA1c is 6.8 percent and Blood Sugar is 120" and let ArogyaMitra's audio interpreter extract the numeric biomarkers.
                </p>

                <div className="relative py-6">
                  <button
                    onClick={() => {
                      if (isRecording) {
                        setIsRecording(false);
                      } else {
                        handleSimulateVoiceInput();
                      }
                    }}
                    className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto transition cursor-pointer shadow ${
                      isRecording ? 'bg-red-600 text-white animate-pulse' : 'bg-teal-600 text-white hover:bg-teal-700'
                    }`}
                  >
                    <Mic className="w-6 h-6" />
                  </button>
                  {isRecording && (
                    <span className="absolute bottom-2 left-1/2 -translate-x-1/2 text-[10px] font-bold text-red-600 uppercase tracking-widest">
                      Recording Vitals...
                    </span>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-gray-500 block text-left">Speech Statement (Type here to simulate audio voice-first dictation)</label>
                  <input
                    type="text"
                    placeholder="e.g. My Fasting Blood Sugar is 115 and Total Cholesterol is 195"
                    value={typedVoiceInput}
                    onChange={(e) => setTypedVoiceInput(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold focus:outline-none text-gray-800"
                  />
                  <button
                    onClick={handleSimulateVoiceInput}
                    disabled={isRecording}
                    className="w-full py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-lg transition cursor-pointer"
                  >
                    Simulate Speech Extraction
                  </button>
                </div>
              </div>

              {voiceParsedResult ? (
                <div className="bg-teal-50/40 border border-teal-100 p-6 rounded-xl space-y-4 shadow-sm flex flex-col justify-between">
                  <div>
                    <h4 className="font-bold text-sm text-teal-800 uppercase tracking-wider flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4 text-teal-600" />
                      Acoustic Extraction Successful
                    </h4>
                    <p className="text-xs text-gray-600 leading-relaxed mt-2">
                      Whisper Speech-To-Text matched the following clinical values:
                    </p>

                    <div className="grid grid-cols-2 gap-4 mt-4 text-xs font-mono">
                      <div className="p-3 bg-white border rounded-lg">
                        <span className="text-[10px] text-gray-400 block font-bold uppercase">Biomarker</span>
                        <span className="font-bold text-gray-800">{voiceParsedResult.paramName}</span>
                      </div>
                      <div className="p-3 bg-white border rounded-lg">
                        <span className="text-[10px] text-gray-400 block font-bold uppercase">Value Extracted</span>
                        <span className="font-bold text-teal-700">{voiceParsedResult.value} {voiceParsedResult.unit}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={handleConfirmVoiceParam}
                      className="flex-1 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-lg shadow transition cursor-pointer"
                    >
                      Confirm & Save Biomarker
                    </button>
                    <button
                      onClick={() => setVoiceParsedResult(null)}
                      className="px-4 py-2 bg-white border hover:bg-gray-50 text-gray-600 text-xs font-bold rounded-lg transition cursor-pointer"
                    >
                      Discard
                    </button>
                  </div>
                </div>
              ) : (
                <div className="bg-white border p-6 rounded-xl space-y-3 shadow-sm flex flex-col justify-center text-center text-gray-500">
                  <Activity className="w-8 h-8 text-gray-300 mx-auto" />
                  <p className="text-xs font-bold">Speech Transcription Output Terminal</p>
                  <p className="text-[10px] text-gray-400">Processed transcript parameters will appear here for confirmation prior to storage save action.</p>
                </div>
              )}
            </div>
          </div>
        )}

      </div>

    </div>
  );
};
