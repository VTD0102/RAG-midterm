import { useState } from "react";
import { v4 as uuidv4 } from "uuid";
import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";

export default function Home() {
  const [sessionId, setSessionId] = useState<string>(uuidv4());

  const handleNewSession = () => setSessionId(uuidv4());
  const handleSelectSession = (id: string) => setSessionId(id);

  return (
    <main
      style={{
        display: "flex",
        height: "100dvh",
        overflow: "hidden",
        background: "var(--bg-base)",
      }}
    >
      <Sidebar
        currentSessionId={sessionId}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
      />
      <ChatWindow sessionId={sessionId} />
    </main>
  );
}
