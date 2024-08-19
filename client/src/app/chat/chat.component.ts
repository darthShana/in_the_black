import {Component, OnDestroy, OnInit, signal} from '@angular/core';
import {MatFormField} from "@angular/material/form-field";
import {MatInput} from "@angular/material/input";
import {CommonModule} from "@angular/common";

import {Subject, takeUntil} from "rxjs";
import {AssistantService} from "../service/assistant.service";
import {MatExpansionModule} from "@angular/material/expansion";

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [
    CommonModule, MatFormField, MatInput, MatExpansionModule
  ],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss'
})
export class ChatComponent implements OnInit, OnDestroy{

  unsubscribe: Subject<void> = new Subject();
  conversationList: string[] = []
  conversationMap: Map<string, Record<string, unknown>> = new Map();
  readonly panelOpenState = signal(false);
  constructor(private assistantService: AssistantService) {
  }
  async ngOnInit() {
    await this.assistantService.initialize()

    this.assistantService.conversationMapSubject
      .pipe(takeUntil(this.unsubscribe))
      .subscribe(conversationMap => this.conversationMap = conversationMap)
    this.assistantService.conversationSubject
      .pipe(takeUntil(this.unsubscribe))
      .subscribe(conversation => this.conversationList.push(conversation))
  }

  ngOnDestroy(): void {
    this.unsubscribe.next();
    this.unsubscribe.complete();
  }

  protected stream(query: string){
    this.assistantService.stream(query)
  }
}
