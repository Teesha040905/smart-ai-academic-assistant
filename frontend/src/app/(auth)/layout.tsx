export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <div className="h-screen max-h-screen w-screen overflow-hidden bg-[#043634]">{children}</div>;
}
