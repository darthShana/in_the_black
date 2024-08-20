import {Component, HostBinding, Input, OnInit, SimpleChanges} from '@angular/core';
import {CommonModule} from "@angular/common";
import {MatCardModule} from "@angular/material/card";
import {MatProgressSpinner} from "@angular/material/progress-spinner";

export type Thought = {
  aiResponse: string;
  directToolResult: any;
  display: boolean;
}

@Component({
  selector: 'app-chat-bubble',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatProgressSpinner],
  templateUrl: './chat-bubble.component.html',
  styleUrl: './chat-bubble.component.scss'
})
export class ChatBubbleComponent implements OnInit{

  @Input() thought?:Record<string, unknown>;
  humanRequest!:string ;
  thoughtMap: Map<string, Thought> = new Map()
  thoughtTime: Map<string, Number> = new Map()
  thoughtOrder:string[] = []
  toolUseInProgress: boolean = false

  @HostBinding('class')
  get position(): string {
    if (this.humanRequest) {
      return 'right-align';
    }

    return 'left-align';
  }

  ngOnInit() {
    if(this.thought && this.thought["human"]){
      this.humanRequest = this.thought["human"] as string
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
          this.toolUseInProgress = newThought['tool_use_in_progress'] as boolean;

          // @ts-ignore
          if (newThought["content"] && newThought["content"][0] && newThought["content"][0].text) {
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
}
