"use client";
import "./globals.css";
import { Toaster } from "react-hot-toast";
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <title>VyapaarSetu — ONDC MSE Onboarding</title>
        <meta name="description" content="AI-powered MSE onboarding for ONDC TEAM Initiative" />
      </head>
      <body className="bg-gray-50 text-gray-900 antialiased">
        {children}
        <Toaster position="top-right" />
      </body>
    </html>
  );
}
