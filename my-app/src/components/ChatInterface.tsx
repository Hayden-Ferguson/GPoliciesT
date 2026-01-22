import { ChatGPT } from "../ChatGPT";
import { AssistantRuntimeProvider, useLocalRuntime } from "@assistant-ui/react";

interface ChatInterfaceProps {
    threadId: string;
    onMessageSent?: (text: string) => void;
}

export function ChatInterface({ threadId, onMessageSent }: ChatInterfaceProps) {
    const runtime = useLocalRuntime({
        run: async function* ({ messages }: { messages: readonly any[] }) {
            if (messages.length === 0) return;
            const lastMessage = messages[messages.length - 1];
            const text = lastMessage.content.find((c: any) => c.type === "text")?.text;

            if (!text) return;

            // Notify parent about the message (e.g. for renaming the thread)
            if (messages.length === 1 && onMessageSent) {
                onMessageSent(text);
            }

            try {
                const response = await fetch("http://localhost:8000/query", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        question: text,
                        thread_id: threadId,
                    }),
                });

                if (!response.ok) {
                    throw new Error(`API Error: ${response.statusText}`);
                }

                const data = await response.json();

                yield {
                    content: [
                        {
                            type: "text",
                            text: data.answer,
                        },
                    ],
                };
            } catch (error) {
                yield {
                    content: [
                        {
                            type: "text",
                            text: `Error: ${error instanceof Error ? error.message : "Unknown error"}`,
                        },
                    ],
                };
            }
        },
    });

    return (
        <AssistantRuntimeProvider runtime={runtime}>
            <ChatGPT />
        </AssistantRuntimeProvider>
    );
}
