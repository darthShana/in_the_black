import {Component, OnDestroy, OnInit} from '@angular/core';
import {Subject, takeUntil} from "rxjs";
import {AssistantService} from "../service/assistant.service";
import untruncateJson from "untruncate-json";
import {CommonModule} from "@angular/common";
import {BankTransactionsComponent} from "./bank-transactions/bank-transactions.component";
import {EndOfYearReportsComponent} from "./end-of-year-reports/end-of-year-reports.component";

@Component({
  selector: 'app-tool-results',
  standalone: true,
  imports: [CommonModule, BankTransactionsComponent, EndOfYearReportsComponent],
  templateUrl: './tool-results.component.html',
  styleUrl: './tool-results.component.scss'
})
export class ToolResultsComponent implements OnInit, OnDestroy{

  unsubscribe: Subject<void> = new Subject();
  protected directToolResult: any = {};
  protected showEndOfYearReports: boolean = false;
  protected showTransactions: boolean = false;
  protected eoyReports: any;

  constructor(private assistantService: AssistantService) {
  }
  ngOnDestroy(): void {
    this.unsubscribe.next();
    this.unsubscribe.complete();
  }

  async ngOnInit() {
    this.assistantService.toolContentSubject
      .pipe(takeUntil(this.unsubscribe))
      .subscribe(json => {
        json = json.substring(json.indexOf("```json") + 7)
        if (json.indexOf("```") != -1) {
          json = json.substring(0, json.lastIndexOf("```"))
        }
        const fixJson = untruncateJson(json)
        this.directToolResult = JSON.parse(fixJson)
      })

    this.assistantService.toolProgressSubject
      .pipe(takeUntil(this.unsubscribe))
      .subscribe(completedTool => {
        console.log("completed tool in tool results:"+completedTool)
        if(completedTool === "load_transactions"){
          this.showTransactions = true;
        }
        if(completedTool === "classify_transactions"){
          this.showTransactions = true;
        }
        if(completedTool === "save_transactions"){
          this.showTransactions = true;
        }
        if(completedTool === "generate_end_of_year_reports"){
          this.showTransactions = false;
          this.showEndOfYearReports = true
        }
      })

    this.assistantService.toolResultsSubject
      .pipe(takeUntil(this.unsubscribe))
      .subscribe(json => {
        const modifiedString = json.replace(/'/g, '"').replace(/Decimal\(/g, '').replace(/\)/g, '');
        this.eoyReports = JSON.parse(modifiedString, this.decimalReviver);
      })

  }

// Custom reviver function to handle Decimal values
  private decimalReviver(key: string, value: any): any {
    if (typeof value === 'string' && value.startsWith('Decimal(')) {
      const decimalValue = value.replace(/Decimal\('?([^']+)'?\)/, '$1');
      return parseFloat(decimalValue);
    }
    return value;
  }

}
