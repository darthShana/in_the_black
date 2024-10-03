import {Component, OnDestroy, OnInit} from '@angular/core';
import {Subject, takeUntil} from "rxjs";
import {AssistantService} from "../service/assistant.service";
import {CommonModule} from "@angular/common";
import {TransactionsComponent} from "./transactions/transactions.component";
import {EndOfYearReportsComponent} from "./end-of-year-reports/end-of-year-reports.component";
import {BarChartComponent} from "../bar-chart/bar-chart.component";
import {PieChartComponent} from "../pie-chart/pie-chart.component";
import {MatIconModule} from "@angular/material/icon";
import {CompanyOverviewComponent} from "./company-overview/company-overview.component";
import {decimalReviver} from "../utils/decimal-utils";

@Component({
  selector: 'app-tool-results',
  standalone: true,
  imports: [CommonModule, TransactionsComponent, EndOfYearReportsComponent, BarChartComponent, PieChartComponent, MatIconModule, CompanyOverviewComponent],
  templateUrl: './tool-results.component.html',
  styleUrl: './tool-results.component.scss'
})
export class ToolResultsComponent implements OnInit, OnDestroy{

  unsubscribe: Subject<void> = new Subject();
  protected showEndOfYearReports: boolean = false;
  protected showTransactions: boolean = false;
  protected showCompanyOverview: boolean = false;
  protected toolResult: any;

  constructor(private assistantService: AssistantService) {
  }
  ngOnDestroy(): void {
    this.unsubscribe.next();
    this.unsubscribe.complete();
  }

  private transactionTools = new Set(['load_transactions', 'classify_bank_transactions', 'classify_property_management_transactions', 'classify_vendor_transactions']);
  async ngOnInit() {

    this.assistantService.toolResultsSubject
      .pipe(takeUntil(this.unsubscribe))
      .subscribe(event => {
        let completedTool = event.name
        console.log("completed tool in tool results:"+completedTool)

        let json = event.content
        const modifiedString = json.replace(/'/g, '"').replace(/Decimal\(/g, '').replace(/\)/g, '');
        this.toolResult = JSON.parse(modifiedString, decimalReviver);

        if(this.transactionTools.has(completedTool)){
          this.showTransactions = true;
          this.showEndOfYearReports = false
          this.showCompanyOverview = false
        }
        if(completedTool === "generate_end_of_year_reports"){
          this.showTransactions = false;
          this.showEndOfYearReports = true
          this.showCompanyOverview = false
        }
        if(completedTool === "company_overview"){
          this.showTransactions = false;
          this.showEndOfYearReports = false
          this.showCompanyOverview = true
        }
      })

  }



}
