import "./globals.css";

export const metadata = {
  title: "SportSaaS",
  description: "Sport SaaS",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}

