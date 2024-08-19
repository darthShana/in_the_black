import { Injectable } from '@angular/core';
import {Client, Thread} from "@langchain/langgraph-sdk";
import {BehaviorSubject, Subject} from "rxjs";
import {v4 as uuid} from "uuid";
// @ts-ignore
import {StreamEvent} from "@langchain/langgraph-sdk/dist/types";

@Injectable({
  providedIn: 'root'
})
export class AssistantService {

  private conversationMap: Map<string, Record<string, unknown>> = new Map();
  public conversationMapSubject: BehaviorSubject<Map<string, Record<string, unknown>>> = new BehaviorSubject(this.conversationMap)
  public conversationSubject: Subject<string> = new Subject()
  public bankTransactionsSubject: Subject<any> = new Subject()
  public toolResultsSubject: Subject<string> = new Subject()
  public toolProgressSubject: Subject<string> = new Subject()

  client = new Client();
  thread?: Thread;
  assistantId = "agent"

  constructor() { }

  async initialize(){
    this.thread = await this.client.threads.create();
  }

  async stream(prompt: string) {
    const input = {"messages": [{"role": "human", "content": "process transactions from company account in file Export20240727172157.csv"}]}

    if (this.thread) {
      const streamResponse = this.client.runs.stream(
        this.thread["thread_id"],
        this.assistantId,
        {
          input: input,
          streamMode: "messages",
        }
      );
      await this.streamResponses(streamResponse, prompt);
    }
  }

  private async streamResponses(streamResponse: AsyncGenerator<{ event: StreamEvent; data: any }>, prompt: string) {
    let runId: string | undefined;
    for await (const message of streamResponse) {
      // console.log(`Receiving new event of type: ${chunk.event}...`);
      // console.log(chunk.data);
      // console.log("\n\n");
      console.log(`content: ${JSON.stringify(message)}`);

      if (message.event === "metadata") {
        const data = message.data as Record<string, unknown>;
        // console.log(`Metadata: Run ID - ${data["run_id"]}`);
        runId = data["run_id"] as string
        this.conversationSubject.next(runId + "-a")
        this.conversationMap.set(runId + "-a", {
          "id": uuid(),
          "human": prompt
        })
        this.conversationMapSubject.next(this.conversationMap)

      } else if (message.event === "messages/partial") {

        for (const dataItem of message.data as Record<string, unknown>[]) {
          if (!runId) {
            return
          }

          // console.log(`content: ${JSON.stringify(dataItem)}`);

        }
      } else if (message.event === "messages/complete") {
        // console.log(`complete message ${JSON.stringify(message)}`)

        for (const parts of message.data) {


          if (parts.type === "tool" && (parts.name == 'classify_transactions' || parts.name == 'load_transactions')) {
            if (parts.content && (typeof parts.content === 'string') && (parts.content as string).startsWith("{\"bank_transactions\"")) {
              console.log("bank_transactions------")
              const transactions = JSON.parse(parts.content)
              this.bankTransactionsSubject.next(transactions)
            }
          }
          if (parts.type === "tool"){
            this.toolProgressSubject.next(parts.name)
          }
          // if (parts['tool_calls'][0].name == 'AskHuman') {
            // ask the human a question
          // }

        }

      }
    }
  }

  async confirmTransactions(transactions: any[]){
    if (this.thread) {
      console.log('in here updateTransactionType')
      const state = await this.client.threads.getState(this.thread['thread_id']);
      // @ts-ignore
      console.log(state['values']["messages"].at(-1))
      // @ts-ignore
      const toolCallId = state['values']["messages"].at(-1)['tool_calls'][0]['id'];

      const toolMessage = [{"tool_call_id": toolCallId, "type": "tool", "content": JSON.stringify({"foo": "goo"})}];
      await this.client.threads.updateState(
        this.thread["thread_id"],
        {
          values: {
            "messages": toolMessage
          },
          asNode: 'ask_human'
        }
      )
      const streamResponse = this.client.runs.stream(
        this.thread["thread_id"],
        this.assistantId,
        {
          input: null,
          streamMode: "messages",
        }
      );
      await this.streamResponses(streamResponse, "")
    }
  }

}
