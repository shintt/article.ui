"use client";

import { useChat } from "ai/react";
import { SendHorizonalIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function Home() {
  const { messages, input, handleInputChange, handleSubmit } = useChat({
    api: "http://127.0.0.1:8000/api/chat",
    streamProtocol: "data",
  });

  return (
    <div className="p-8">
      {messages.map((message) => (
        <div key={message.id}>
          {message.role === "user" ? "User: " : "AI: "}
          {message.content}
          {message.toolInvocations && message.toolInvocations.length > 0 && (
            <div className="flex flex-col gap-4">
              {message.toolInvocations.map((toolInvocation) => {
                const { toolName, toolCallId, state } = toolInvocation;

                if (state === "result") {
                  const { result } = toolInvocation;

                  return (
                    <div key={toolCallId}>
                      {toolName === "render_bar_chart_rsc" ? (
                        result
                      ) : (
                        <pre>{JSON.stringify(result, null, 2)}</pre>
                      )}
                    </div>
                  );
                }
              })}
            </div>
          )}
        </div>
      ))}

      <form
        className="flex w-full max-w-sm items-center space-x-2"
        onSubmit={handleSubmit}
      >
        <Input
          name="prompt"
          placeholder="What you want to know?"
          value={input}
          onChange={handleInputChange}
          autoComplete="off"
        />
        <Button type="submit">
          <SendHorizonalIcon />
        </Button>
      </form>
    </div>
  );
}
