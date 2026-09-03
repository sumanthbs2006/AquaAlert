import React from 'react';
import { 
  Layers, 
  Cpu, 
  Database, 
  Satellite, 
  Radio, 
  CloudRain, 
  AlertCircle, 
  Code2,
  Award
} from 'lucide-react';
import { getTranslation } from '../i18n';

export default function AboutPage({ currentLang = 'en' }) {
  const t = getTranslation(currentLang);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      {/* Hero Banner */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-cyan-950 border border-slate-800 p-6 sm:p-8 rounded-3xl shadow-2xl relative overflow-hidden">
        <div className="relative z-10 space-y-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1.5">
              <Award className="w-3.5 h-3.5" />
              {t.aboutTag}
            </span>
            <span className="text-xs text-slate-400 font-semibold">
              {t.aboutTheme}
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            {t.aboutHeroTitle}
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 max-w-3xl leading-relaxed">
            {t.aboutHeroDesc}
          </p>
        </div>
      </div>

      {/* 6 Heterogeneous Data Ingestion Layers */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-cyan-400" />
          <h2 className="text-base sm:text-lg font-bold text-white uppercase tracking-wider">
            {t.aboutSec1Title}
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl space-y-2">
            <div className="w-9 h-9 rounded-lg bg-cyan-950 flex items-center justify-center text-cyan-400 border border-cyan-800">
              <Satellite className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-white">{t.aboutSatelliteTitle}</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              {t.aboutSatelliteDesc}
            </p>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl space-y-2">
            <div className="w-9 h-9 rounded-lg bg-sky-950 flex items-center justify-center text-sky-400 border border-sky-800">
              <Radio className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-white">{t.aboutRadarTitle}</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              {t.aboutRadarDesc}
            </p>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl space-y-2">
            <div className="w-9 h-9 rounded-lg bg-emerald-950 flex items-center justify-center text-emerald-400 border border-emerald-800">
              <CloudRain className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-white">{t.aboutAwsTitle}</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              {t.aboutAwsDesc}
            </p>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl space-y-2">
            <div className="w-9 h-9 rounded-lg bg-blue-950 flex items-center justify-center text-blue-400 border border-blue-800">
              <span className="text-lg">🌊</span>
            </div>
            <h3 className="text-sm font-bold text-white">{t.aboutRiverTitle}</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              {t.aboutRiverDesc}
            </p>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl space-y-2">
            <div className="w-9 h-9 rounded-lg bg-amber-950 flex items-center justify-center text-amber-400 border border-amber-800">
              <Database className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-white">{t.aboutGisTitle}</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              {t.aboutGisDesc}
            </p>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl space-y-2">
            <div className="w-9 h-9 rounded-lg bg-purple-950 flex items-center justify-center text-purple-400 border border-purple-800">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-white">{t.aboutNwpTitle}</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              {t.aboutNwpDesc}
            </p>
          </div>
        </div>
      </div>

      {/* Hydrological Mathematical Modeling */}
      <div className="bg-slate-900 border border-slate-800 p-5 sm:p-6 rounded-2xl shadow-xl space-y-4">
        <div className="flex items-center gap-2">
          <Code2 className="w-5 h-5 text-cyan-400" />
          <h2 className="text-base sm:text-lg font-bold text-white uppercase tracking-wider">
            {t.aboutSec2Title}
          </h2>
        </div>

        <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1.5">
            <strong className="text-cyan-400 text-sm block">{t.aboutZrTitle}</strong>
            <p className="font-mono text-slate-400 bg-slate-900 p-2 rounded overflow-x-auto">
              Z = a · R^b  ⇒  R = ((10^(dBZ / 10)) / 200)^(1 / 1.6)
            </p>
            <p>{t.aboutZrDesc}</p>
          </div>

          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1.5">
            <strong className="text-cyan-400 text-sm block">{t.aboutApiTitle}</strong>
            <p className="font-mono text-slate-400 bg-slate-900 p-2 rounded overflow-x-auto">
              API_t = Σ (k^i · P_(t-i))
            </p>
            <p>{t.aboutApiDesc}</p>
          </div>

          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1.5">
            <strong className="text-cyan-400 text-sm block">{t.aboutXaiTitle}</strong>
            <p>{t.aboutXaiDesc}</p>
          </div>
        </div>
      </div>

      {/* Decision Support Disclaimer */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl text-xs space-y-2">
        <div className="flex items-center gap-2 text-amber-400 font-bold">
          <AlertCircle className="w-4 h-4" />
          <span>{t.aboutDisclaimerTitle}</span>
        </div>
        <p className="text-slate-400 leading-relaxed">
          {t.aboutDisclaimerDesc}
        </p>
      </div>
    </div>
  );
}
