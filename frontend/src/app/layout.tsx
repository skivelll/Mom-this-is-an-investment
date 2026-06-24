import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/shared/components/query-provider";

export const metadata: Metadata = {
  title: "Мам, это инвестиция",
  description: "Коллекции комиксов, манги, фигурок и другого гик-мерча.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
