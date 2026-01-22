import { useState, useEffect } from "react";
import { Sidebar, type Thread } from "./components/Sidebar";
import { ChatInterface } from "./components/ChatInterface";

export function App() {
  const [threads, setThreads] = useState<Thread[]>(() => {
    const saved = localStorage.getItem("threads");
    return saved ? JSON.parse(saved) : [];
  });
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);

  useEffect(() => {
    localStorage.setItem("threads", JSON.stringify(threads));
  }, [threads]);

  const createNewThread = async () => {
    try {
      const response = await fetch("http://localhost:8000/query/threads", {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to create thread");
      const data = await response.json();

      const newThread: Thread = {
        id: data.thread_id,
        title: "New Chat",
        createdAt: Date.now(),
      };

      setThreads((prev) => [newThread, ...prev]);
      setActiveThreadId(newThread.id);
    } catch (error) {
      console.error("Error creating thread:", error);
    }
  };

  const deleteThread = (threadId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setThreads((prev) => prev.filter((t) => t.id !== threadId));
    if (activeThreadId === threadId) {
      setActiveThreadId(null);
    }
  };

  const handleMessageSent = (text: string) => {
    setThreads(prev => prev.map(t =>
      t.id === activeThreadId && t.title === "New Chat"
        ? { ...t, title: text.slice(0, 30) + (text.length > 30 ? "..." : "") }
        : t
    ));
  };

  useEffect(() => {
    if (threads.length === 0 && !activeThreadId) {
      createNewThread();
    } else if (threads.length > 0 && !activeThreadId) {
      setActiveThreadId(threads[0].id);
    }
  }, [threads.length, activeThreadId]);

  return (
    <div className="flex h-screen w-full bg-[#212121]">
      <Sidebar
        threads={threads}
        activeThreadId={activeThreadId}
        onSelectThread={setActiveThreadId}
        onNewChat={createNewThread}
        onDeleteThread={deleteThread}
      />

      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {activeThreadId ? (
          <ChatInterface
            threadId={activeThreadId}
            key={activeThreadId}
            onMessageSent={handleMessageSent}
          />
        ) : (
          <div className="flex flex-1 items-center justify-center text-zinc-500">
            Select a chat or start a new one.
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
