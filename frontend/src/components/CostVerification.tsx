'use client';

import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { DollarSign, ShieldCheck, X, CheckCircle2 } from 'lucide-react';

export default function CostVerification() {
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const costItems = [
    { service: 'AWS EC2 (t2.micro)', spec: '1 GB RAM + 2 GB Swap', cost: '$0.00', status: 'Free Tier' },
    { service: 'Supabase Postgres', spec: 'RLS DB + Auth', cost: '$0.00', status: 'Free Tier' },
    { service: 'Groq LPU API', spec: 'Llama 3.3 70B Fast Inference', cost: '$0.00', status: 'Free Tier' },
    { service: 'Cloudflare Tunnel', spec: 'Zero-Trust WSS / HTTPS Edge', cost: '$0.00', status: 'Free Tier' },
    { service: 'Vercel App Hosting', spec: 'Next.js 14 WebGL Edge', cost: '$0.00', status: 'Free Tier' },
  ];

  const modalContent = isOpen ? (
    <div className="fixed inset-0 z-[99999] flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <div className="relative w-full max-w-lg bg-neutral-900 border border-neutral-800 rounded-xl p-6 shadow-2xl font-sans text-neutral-200">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-neutral-800 pb-4 mb-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-semibold text-white tracking-wide">
              Infrastructure Cost Audit
            </h3>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="text-neutral-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Total Cost Banner */}
        <div className="bg-emerald-950/30 border border-emerald-500/20 rounded-lg p-4 mb-5 flex items-center justify-between">
          <div>
            <p className="text-xs text-emerald-400 font-mono uppercase">Total Monthly Spend</p>
            <p className="text-2xl font-bold text-emerald-300 font-mono">$0.00 USD</p>
          </div>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" /> 100% Free Tier Verified
          </span>
        </div>

        {/* Cost Breakdown Table */}
        <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
          {costItems.map((item, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-2.5 rounded-lg bg-neutral-950/50 border border-neutral-800/60 text-xs"
            >
              <div>
                <p className="font-medium text-neutral-200">{item.service}</p>
                <p className="text-[11px] text-neutral-500 font-mono">{item.spec}</p>
              </div>
              <div className="text-right font-mono">
                <p className="font-semibold text-emerald-400">{item.cost}</p>
                <p className="text-[10px] text-neutral-500">{item.status}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Modal Footer */}
        <div className="mt-5 pt-4 border-t border-neutral-800 flex justify-end">
          <button
            onClick={() => setIsOpen(false)}
            className="px-4 py-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-xs font-medium text-neutral-300 transition-colors"
          >
            Close Audit
          </button>
        </div>
      </div>
    </div>
  ) : null;

  return (
    <>
      {/* Header Cost Trigger Badge */}
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 bg-emerald-950/40 border border-emerald-500/30 hover:border-emerald-500/60 transition-all px-3 py-1.5 rounded-lg text-xs font-mono text-emerald-400 backdrop-blur-md shadow-lg shadow-emerald-950/20"
      >
        <DollarSign className="w-4 h-4 text-emerald-400 animate-pulse" />
        <span>INFRA COST:</span>
        <span className="font-bold text-emerald-300">$0.00 / mo</span>
      </button>

      {/* Portal to Body */}
      {mounted && modalContent && createPortal(modalContent, document.body)}
    </>
  );
}