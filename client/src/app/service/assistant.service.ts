import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs/internal/BehaviorSubject';
import { v4 as uuid } from 'uuid';
import { Assistant, Client, Thread } from '@langchain/langgraph-sdk';
import { Subject } from 'rxjs/internal/Subject';

@Injectable({
  providedIn: 'root',
})
export class AssistantService {
  public conversationOrder: string[] = [];
  public conversationOrderSubject: Subject<string[]> = new BehaviorSubject(
    this.conversationOrder
  );

  public toolResultsSubject: Subject<string> = new Subject();

  public streamResults: Map<
    string,
    Record<string, unknown & { content: { text: string }[] } & any>
  > = new Map();
  public streamResultsSubject: BehaviorSubject<
    Map<string, Record<string, unknown & { content: { text: string }[] } & any>>
  > = new BehaviorSubject(this.streamResults);
  public bankTransactionsSubject: Subject<any> = new Subject()
  public toolProgressSubject: Subject<string> = new Subject()


  // client = new Client()
  client = new Client({
    apiUrl: "https://in-the-black-deployment1-868b23288fc75ff39ea9e5d8aa6b5c27.default.us.langgraph.app",
    defaultHeaders: {
      'x-api-key': 'ls__46f92d1f04484620a7602442d163936c',
    },
  });
  thread?: Thread;
  assistant?: Assistant;

  constructor() {}

  async stream(prompt: string) {
    const input = {
      messages: [{ role: 'user', content: prompt }],
    };

    if (!this.thread || !this.assistant) {
      return;
    }

    for await (const event of this.client.runs.stream(
      this.thread.thread_id,
      this.assistant.assistant_id,
      { input, streamMode: 'messages' }
    )) {
      const data = event.data as Record<string, unknown & { content: { text: string }[] } & any>;

      if (event.event === 'metadata') {
        this.handleMetadata(data, prompt);
      } else if (event.event === 'messages/partial') {
        this.handlePartial(data);
      } else if (event.event === 'messages/complete') {
        this.handleComplete(data);
      }
    }
  }

  async continue(option: string){
    if (!this.thread || !this.assistant) {
      return;
    }
    const state = await this.client.threads.getState(this.thread['thread_id']);
    // @ts-ignore
    const toolCallId = state['values']["messages"].at(-1)['tool_calls'][0]['id'];
    const toolMessage = [{"tool_call_id": toolCallId, "type": "tool", "content": option}];
    await this.client.threads.updateState(
      this.thread["thread_id"],
      {
        values: {
          "messages": toolMessage
        },
        asNode: 'ask_human'
      }
    )

    for await (const event of this.client.runs.stream(
      this.thread.thread_id,
      this.assistant.assistant_id,
      {
        input: null,
        streamMode: 'messages' }
    )) {
      const data = event.data as Record<
        string,
        unknown & { content: { text: string }[] } & any>;

      if (event.event === 'messages/partial') {
        this.handlePartial(data);
      } else if (event.event === 'messages/complete') {
        this.handleComplete(data);
      }
    }

  }

  handleMetadata(data: any, prompt: string) {
    const runId = data['run_id'] as string;
    this.conversationOrder.push(runId + '-a');
    this.streamResults.set(runId + '-a', {
      id: uuid(),
      type: 'human',
      content: [
        {
          text: prompt,
        },
      ],
    });
    this.streamResultsSubject.next(this.streamResults);
  }

  handlePartial(data: any) {
    for (const dataItem of data as Record<
      string,
      unknown & { content: { text: string }[] } & any
    >[]) {

      // Handle tool call
      if (
        dataItem['content'] &&
        (dataItem['content'] as string).indexOf('```json') != -1
      ) {
        this.toolResultsSubject.next(dataItem['content'])
      } else

      if (dataItem['content'] && dataItem['content'][0] && dataItem['content'][0]['text']) {
        if (this.conversationOrder.indexOf(dataItem['id'] + '-b') === -1) {
          this.conversationOrder.push(dataItem['id'] + '-b');
          this.conversationOrderSubject.next(this.conversationOrder);
        }

        this.streamResults.set(dataItem['id'] + '-b', dataItem);
        this.streamResultsSubject.next(this.streamResults);
      }
    }
  }

  handleComplete(data: any) {
    let parts = data.at(-1)
    if (parts.type === "tool" && (parts.name == 'classify_transactions' || parts.name == 'load_transactions')) {
      if (parts.content && (typeof parts.content === 'string') && (parts.content as string).startsWith("{\"bank_transactions\"")) {
        console.log("bank_transactions------")
        const transactions = JSON.parse(parts.content)
        this.bankTransactionsSubject.next(transactions)
      }
    }
    if (parts.type === "tool"){
      console.log('parts.name: ', parts.name)
      this.toolProgressSubject.next(parts.name)
    }
    if (parts.type === "ai" && parts.tool_calls){
      if(parts.tool_calls[0].name === "AskHuman"){
        console.log('ask human subject.....')
        console.log(data)
        this.conversationOrder.push(parts['id'] + '-b');
        this.streamResults.set(parts['id'] + '-b', {
          id: uuid(),
          type: 'ai',
          content: [
            {
              text: parts.tool_calls[0].args['question'],
            },
          ],
        });
        this.streamResultsSubject.next(this.streamResults);
        this.conversationOrder.push(parts['id'] + '-a');
        this.streamResults.set(parts['id'] + '-a', {
          id: uuid(),
          type: 'human',
          content: [
            {
              options: parts.tool_calls[0].args['options'],
            },
          ],
        });
        this.streamResultsSubject.next(this.streamResults);
      }
    }
  }

  async initialize(user_id: string) {
    if (this.assistant) {
      return;
    }
    this.assistant = await this.client.assistants.create({
      graphId: 'agent',
      config: {
        configurable: {
          model_name: 'openai',
          user_id: user_id,
        },
      },
    });

    this.thread = await this.client.threads.create();
  }
}
