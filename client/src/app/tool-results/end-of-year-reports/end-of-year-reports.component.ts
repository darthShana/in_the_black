import {Component, Input, OnInit} from '@angular/core';
import {AssistantService} from "../../service/assistant.service";
import {CommonModule, JsonPipe} from "@angular/common";
import {MatTableModule} from '@angular/material/table';
import {MatIconModule} from "@angular/material/icon";
import {MatButtonModule, MatFabButton} from "@angular/material/button";

interface ReportLine {
  description: string;
  amount?: string;
  subtitle: boolean;
}
@Component({
  selector: 'app-end-of-year-reports',
  standalone: true,
  imports: [
    JsonPipe,
    MatIconModule,
    MatTableModule, CommonModule, MatFabButton, MatButtonModule
  ],
  templateUrl: './end-of-year-reports.component.html',
  styleUrl: './end-of-year-reports.component.scss'
})
export class EndOfYearReportsComponent implements OnInit{

  @Input() eoyReports!: Record<string, any>;
  protected profitOrLoss: ReportLine[] = []
  protected depreciation: ReportLine[] = []
  protected financialPosition: ReportLine[] = []
  profitOrLossDisplayedColumns: string[] = ['description', 'amount'];
  financialPositionColumns: string[] = ['description', 'amount'];
  depreciationDisplayedColumns: string[] = ['Asset', 'Date Purchased', 'Cost', 'Opening adjusted tax value', 'Rate', 'Method', 'Depreciation', 'Closing adjusted tax value'];

  constructor(private assistantService: AssistantService){}

  ngOnInit(): void {

    console.log("calculating statement_of_profit_or_loss")
    let pOrL = this.eoyReports['statement_of_profit_or_loss']

    this.profitOrLoss.push({description: "Revenue", amount:undefined, subtitle:true})

    for (let revenueItem of pOrL['revenue_items']){
      this.profitOrLoss.push({description: revenueItem['display_name'], amount:revenueItem['balance'], subtitle:false})
    }
    this.profitOrLoss.push({description: "Total Trading Income", amount:pOrL['gross_profit'], subtitle:true})

    for (let expenseItem of pOrL['expenses_items']){
      this.profitOrLoss.push({description: expenseItem['display_name'], amount:expenseItem['balance'], subtitle:false})
    }
    this.profitOrLoss.push({description: "Total Expenses", amount:pOrL['expenses_total'], subtitle:true})


  }

  addAsset(){
    console.log("in here test!!!!")
    this.assistantService.stream("Add asset to my property").then(r => {})
  }



}
