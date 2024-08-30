import {Component, HostBinding, Input, OnInit, SimpleChanges} from '@angular/core';
import untruncateJson from "untruncate-json";
import {MatCardModule} from "@angular/material/card";
import {CommonModule} from "@angular/common";
import {MatProgressSpinner} from "@angular/material/progress-spinner";
import {MatButton} from "@angular/material/button";
import {AssistantService} from "../../service/assistant.service";
import {TransactionsService} from "../../service/transactions.service";
import {Subject, takeUntil} from "rxjs";

export type Thought = {
  aiResponse: string;
  directToolResult: any;
  display: boolean;
}
@Component({
  selector: 'app-chat-bubble',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatProgressSpinner, MatButton],
  templateUrl: './chat-bubble.component.html',
  styleUrl: './chat-bubble.component.scss'
})
export class ChatBubbleComponent implements OnInit{

  unsubscribe: Subject<void> = new Subject();
  @Input() thought?:Record<string, unknown>;
  isUser = false;
  thoughtMap: Map<string, Thought> = new Map()
  thoughtTime: Map<string, Number> = new Map()
  thoughtOrder:string[] = []
  toolUseIbProgress: boolean = false

  constructor(private assistantService: AssistantService, private transactionService: TransactionsService) {
  }

  ngOnDestroy(): void {
    this.unsubscribe.next();
    this.unsubscribe.complete();
  }

    ngOnInit() {
    console.log(this.thought, this.thought && this.thought["type"])
    if(this.thought && this.thought["type"]){
      this.isUser = this.thought["type"] === 'human';
    }


  }

  async ngOnChanges(changes: SimpleChanges) {
    if (changes['thought']){
      const newThought: Record<string, unknown> = changes['thought'].currentValue
      if(newThought) {

        const intermediate_id = newThought["id"] as string;
        let intermediateThoughts = this.thoughtMap.get(intermediate_id)


        if (!intermediateThoughts) {
          console.log(`pushing new intermediate_id:${intermediate_id}`)
          this.thoughtOrder.push(intermediate_id)
          this.thoughtMap.set(intermediate_id, {
            aiResponse: "",
            directToolResult: undefined,
            display: false
          });
        }
        this.thoughtTime.set(intermediate_id, Date.now())
        let latest = this.thoughtMap.get(intermediate_id);

        if(latest) {

          // console.log(newThought)
          this.toolUseIbProgress = newThought['tool_use_in_progress'] as boolean;

          if (newThought["content"] && (newThought["content"] as string).indexOf("```json") != -1) {
            let json = (newThought["content"] as string);
            json = json.substring(json.indexOf("```json") + 7)
            if (json.indexOf("```") != -1) {
              json = json.substring(0, json.lastIndexOf("```"))
            }
            const fixJson = untruncateJson(json)
            // console.log(fixJson)
            latest.directToolResult = JSON.parse(fixJson)
            latest.display = true
            // @ts-ignore
          } else if (newThought["content"] && newThought["content"][0] && newThought["content"][0].text) {
            // @ts-ignore
            latest.aiResponse = newThought["content"][0].text
            latest.display = true
          } else {
            latest.display = false
          }

        }

      }

    }
  }

  async continue(option: string){
    await this.transactionService.confirmFilteredTransactions(option)
  }
}
