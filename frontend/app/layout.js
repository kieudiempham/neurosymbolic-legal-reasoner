import "./globals.css";

export const metadata = {
  title: "Legal QA",
  description: "Minimal frontend for backend QA",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
