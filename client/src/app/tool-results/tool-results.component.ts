import {Component, OnDestroy, OnInit} from '@angular/core';
import {Subject, takeUntil} from "rxjs";
import {AssistantService} from "../service/assistant.service";
import untruncateJson from "untruncate-json";
import {CommonModule} from "@angular/common";
import {BankTransactionsComponent} from "./bank-transactions/bank-transactions.component";

@Component({
  selector: 'app-tool-results',
  standalone: true,
  imports: [CommonModule, BankTransactionsComponent],
  templateUrl: './tool-results.component.html',
  styleUrl: './tool-results.component.scss'
})
export class ToolResultsComponent implements OnInit, OnDestroy{

  unsubscribe: Subject<void> = new Subject();
  protected directToolResult: any = {};

  constructor(private assistantService: AssistantService) {
  }
  ngOnDestroy(): void {
    this.unsubscribe.next();
    this.unsubscribe.complete();
  }

  async ngOnInit() {
    this.assistantService.toolResultsSubject
      .pipe(takeUntil(this.unsubscribe))
      .subscribe(json => {
        json = json.substring(json.indexOf("```json") + 7)
        if (json.indexOf("```") != -1) {
          json = json.substring(0, json.lastIndexOf("```"))
        }
        const fixJson = untruncateJson(json)
        this.directToolResult = JSON.parse(fixJson)
      })
  }

}
