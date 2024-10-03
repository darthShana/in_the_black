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

  public toolContentSubject: Subject<string> = new Subject();

  public streamResults: Map<
    string,
    Record<string, unknown & { content: { text: string }[] } & any>
  > = new Map();
  public streamResultsSubject: BehaviorSubject<
    Map<string, Record<string, unknown & { content: { text: string }[] } & any>>
  > = new BehaviorSubject(this.streamResults);
  public toolResultsSubject: Subject<any> = new Subject()
  public toolProgressSubject: Subject<string> = new Subject()


  // client = new Client()
  client = new Client({
    apiUrl: "https://ht-another-propane-44-77e8f9bf34eb5c32ab43c5c4e6bfba05.default.us.langgraph.app",
    defaultHeaders: {
      'x-api-key': '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',
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
        this.toolContentSubject.next(dataItem['content'])
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

  private toolsWithViews   = new Set(['load_transactions', 'classify_bank_transactions', 'classify_property_management_transactions', 'load_vendor_transactions', 'classify_vendor_transactions', 'generate_end_of_year_reports', 'company_overview']);

  handleComplete(data: any) {
    let parts = data.at(-1)

    if (parts.type === "tool"){
      console.log('completed tool: ', parts.name)
      this.toolProgressSubject.next(parts.name)
    }

    if (parts.type === "tool" && (this.toolsWithViews.has(parts.name))) {
      console.log('handleComplete')
      console.log(parts.content)
      if (parts.content && (typeof parts.content === 'string')) {
        console.log('show tool result')
        this.toolResultsSubject.next(parts)
      }
    }

    if (parts.type === "ai" && parts.tool_calls && parts.tool_calls.length > 0){
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

  async updateTransactions(filterMaps: Record<string, any>[], command: string) {
    if (!this.thread || !this.assistant) {
      return;
    }
    await this.client.threads.updateState(this.thread['thread_id'],
      {
        values:{"transactions": {'transactions': filterMaps}},
        asNode: "ask_human"
      });
    console.log("transactions updated")
    this.continue(command).then()

  }
}
