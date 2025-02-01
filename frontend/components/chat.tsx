import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useChat } from "ai/react";
import { SendHorizonalIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export const Chat = () => {
  const { messages, input, handleInputChange, handleSubmit } = useChat({
    api: "http://127.0.0.1:8000/api/chat",
    streamProtocol: "data",
  });

  return (
    <div className="my-8 w-full flex flex-col items-center">
      <form
        className="flex w-[500px] items-center space-x-1"
        onSubmit={handleSubmit}
      >
        <Input
          name="prompt"
          placeholder="What do you want to know?"
          value={input}
          onChange={handleInputChange}
          autoComplete="off"
        />
        <Button type="submit">
          <SendHorizonalIcon />
        </Button>
      </form>

      {messages.map((message) => (
        <div key={message.id}>
          {message.role === "assistant" && (
            <Markdown remarkPlugins={[remarkGfm]} className="prose">
              {message.content}
            </Markdown>
          )}
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
    </div>
  );
};
