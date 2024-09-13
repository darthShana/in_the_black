import {Component, OnDestroy, OnInit} from '@angular/core';
import {Subject, takeUntil} from "rxjs";
import {AssistantService} from "../service/assistant.service";
import {CommonModule} from "@angular/common";
import {TransactionsComponent} from "./transactions/transactions.component";
import {EndOfYearReportsComponent} from "./end-of-year-reports/end-of-year-reports.component";
import {BarChartComponent} from "../bar-chart/bar-chart.component";
import {PieChartComponent} from "../pie-chart/pie-chart.component";
import {MatIconModule} from "@angular/material/icon";

@Component({
  selector: 'app-tool-results',
  standalone: true,
  imports: [CommonModule, TransactionsComponent, EndOfYearReportsComponent, BarChartComponent, PieChartComponent, MatIconModule],
  templateUrl: './tool-results.component.html',
  styleUrl: './tool-results.component.scss'
})
export class ToolResultsComponent implements OnInit, OnDestroy{

  unsubscribe: Subject<void> = new Subject();
  protected showEndOfYearReports: boolean = false;
  protected showTransactions: boolean = false;
  protected toolResult: any;

  constructor(private assistantService: AssistantService) {
  }
  ngOnDestroy(): void {
    this.unsubscribe.next();
    this.unsubscribe.complete();
  }

  private transactionTools = new Set(['load_transactions', 'classify_bank_transactions', 'classify_property_management_transactions', 'classify_vendor_transactions']);
  async ngOnInit() {

    this.assistantService.toolProgressSubject
      .pipe(takeUntil(this.unsubscribe))
      .subscribe(completedTool => {
        console.log("completed tool in tool results:"+completedTool)
        if(this.transactionTools.has(completedTool)){
          this.showTransactions = true;
          this.showEndOfYearReports = false
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
        this.toolResult = JSON.parse(modifiedString, this.decimalReviver);
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
