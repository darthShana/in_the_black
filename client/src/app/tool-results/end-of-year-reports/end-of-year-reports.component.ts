import {Component, Input, OnInit, inject, viewChild} from '@angular/core';
import {AssistantService} from "../../service/assistant.service";
import {CommonModule, JsonPipe, NgForOf, NgIf} from "@angular/common";
import {MatTableModule} from '@angular/material/table';
import {MatIconModule} from "@angular/material/icon";
import {MatFormFieldModule} from '@angular/material/form-field';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import {MatInputModule} from '@angular/material/input';
import {MatSelectModule} from '@angular/material/select';
import {MatButtonModule, MatFabButton} from "@angular/material/button";
import {
  MatDialog,
  MatDialogTitle,
  MatDialogContent,
} from '@angular/material/dialog';
import {MatMenuModule, MatMenuTrigger} from "@angular/material/menu";
import {ProfileService} from "../../service/profile.service";
import {MatDatepicker, MatDatepickerInput, MatDatepickerToggle} from "@angular/material/datepicker";
import {provideNativeDateAdapter} from '@angular/material/core';

interface ProfitOrLossReportLine {
  description: string;
  amount?: string;
  subtitle: boolean;
}

interface IncomeReportLine {
  description: string;
  amount: string
}

interface DepreciationReportLine {
  asset: string;
  date_purchase: string;
  cost: string;
  opening_value: string;
  rate: string;
  method: string;
  depreciation: string;
  closing_value: string;
}

@Component({
  selector: 'app-end-of-year-reports',
  standalone: true,
  imports: [
    JsonPipe,
    MatIconModule,
    MatTableModule, CommonModule, MatFabButton, MatButtonModule, MatMenuModule
  ],
  templateUrl: './end-of-year-reports.component.html',
  styleUrl: './end-of-year-reports.component.scss'
})
export class EndOfYearReportsComponent implements OnInit{

  @Input() eoyReports!: Record<string, any>;

  readonly menuTrigger = viewChild.required(MatMenuTrigger);
  readonly dialog = inject(MatDialog);


  protected profitOrLoss: ProfitOrLossReportLine[] = []
  protected taxableIncome: IncomeReportLine[] = []
  protected depreciation: DepreciationReportLine[] = []
  profitOrLossDisplayedColumns: string[] = ['description', 'amount'];
  depreciationDisplayedColumns: string[] = ['asset', 'date_purchase', 'cost', 'opening_value', 'rate', 'method', 'depreciation', 'closing_value'];

  constructor(private assistantService: AssistantService){}

  ngOnInit(): void {

    console.log("display statement_of_profit_or_loss")
    let pOrL = this.eoyReports['statement_of_profit_or_loss']
    let tax = this.eoyReports['tax']

    this.profitOrLoss.push({description: "Revenue", amount:undefined, subtitle:true})

    for (let revenueItem of pOrL['revenue_items']){
      this.profitOrLoss.push({description: revenueItem['display_name'], amount:revenueItem['balance'], subtitle:false})
    }
    this.profitOrLoss.push({description: "Total Trading Income", amount:pOrL['gross_profit'], subtitle:true})

    for (let expenseItem of pOrL['expenses_items']){
      this.profitOrLoss.push({description: expenseItem['display_name'], amount:expenseItem['balance'], subtitle:false})
    }
    this.profitOrLoss.push({description: "Total Expenses", amount:pOrL['expenses_total'], subtitle:true})


    console.log("display depreciation")
    for (let item of tax['depreciation']){
      this.depreciation.push({asset: item['asset'], date_purchase: item['date_purchase'], cost: item['cost'], opening_value: item['opening_value'], rate: item['rate'], method: item['method'], depreciation: item['depreciation'], closing_value: item['closing_value']})
    }
    this.taxableIncome.push({description: 'Total Rents', amount: tax['income']['total_rents']})
    this.taxableIncome.push({description: `Other Income (${tax['income']['other_income_description']})`, amount: tax['income']['total_income']})
    this.taxableIncome.push({description: 'Total Income', amount: tax['income']['total_income']})

  }

  openDialog() {
    this.dialog.open(AddAssetDialog);
  }

}

@Component({
  selector: 'add-asset-dialog',
  templateUrl: 'add-asset-dialog.html',
  standalone: true,
  providers: [provideNativeDateAdapter()],
  imports: [ReactiveFormsModule, CommonModule, MatDialogTitle, MatDialogContent, MatFormFieldModule, MatInputModule, MatSelectModule, NgForOf, NgIf, MatDatepickerInput, MatDatepickerToggle, MatDatepicker],
})
export class AddAssetDialog {

  data = {
    available_asset_types: []
  }
  assetFrom = new FormGroup({
    assetType: new FormControl(''),
    installDate: new FormControl(''),
    installValue: new FormControl('')
  })

  constructor(private profileService: ProfileService, private assistantService: AssistantService) {
    this.data.available_asset_types = profileService.metadata['available_asset_types'];
  }

  addAsset() {
    console.log(this.assetFrom.value.assetType)
    console.log(this.assetFrom.value.installDate)
    console.log(this.assetFrom.value.installValue)
    this.assistantService.stream(
      `add the following asset to my property.
      asset_type:${this.assetFrom.value.assetType},
      installation_date:${this.assetFrom.value.installDate},
      installation_value:${this.assetFrom.value.installValue}`,
      false
    )
      .then(r => console.log("done adding asset"))
  }
}
