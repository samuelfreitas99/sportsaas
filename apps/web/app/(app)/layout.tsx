import AuthGate from "./AuthGate";

export default function PrivateLayout({ children }: { children: React.ReactNode }) {
  return <AuthGate>{children}</AuthGate>;
}
