import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { PlusIcon, MessageSquare, Trash2 } from "lucide-react";

export interface Thread {
    id: string;
    title?: string;
    createdAt: number;
}

interface SidebarProps {
    threads: Thread[];
    activeThreadId: string | null;
    onSelectThread: (threadId: string) => void;
    onNewChat: () => void;
    onDeleteThread: (threadId: string, e: React.MouseEvent) => void;
    className?: string;
}

export function Sidebar({
    threads,
    activeThreadId,
    onSelectThread,
    onNewChat,
    onDeleteThread,
    className,
}: SidebarProps) {
    return (
        <div className={cn("flex h-full w-64 flex-col border-r bg-zinc-950 p-4", className)}>
            <Button
                onClick={onNewChat}
                className="mb-4 w-full justify-start gap-2 bg-zinc-800 text-white hover:bg-zinc-700"
                variant="ghost"
            >
                <PlusIcon className="h-4 w-4" />
                New Chat
            </Button>

            <div className="flex-1 overflow-y-auto">
                <div className="flex flex-col gap-2">
                    {threads.length === 0 && (
                        <div className="text-zinc-500 text-sm p-2 text-center">
                            No chats yet.
                        </div>
                    )}
                    {threads.map((thread) => (
                        <div
                            key={thread.id}
                            onClick={() => onSelectThread(thread.id)}
                            className={cn(
                                "group flex w-full cursor-pointer items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors hover:bg-zinc-800/50",
                                activeThreadId === thread.id
                                    ? "bg-zinc-800 text-white"
                                    : "text-zinc-400 hover:text-zinc-100"
                            )}
                        >
                            <div className="flex items-center gap-2 overflow-hidden">
                                <MessageSquare className="h-4 w-4 shrink-0" />
                                <span className="truncate">
                                    {thread.title || "New Chat"}
                                </span>
                            </div>
                            <button
                                onClick={(e) => onDeleteThread(thread.id, e)}
                                className="opacity-0 transition-opacity hover:text-red-400 group-hover:opacity-100"
                            >
                                <Trash2 className="h-4 w-4" />
                            </button>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
