import {Component, OnDestroy, OnInit} from '@angular/core';
import {MatIcon} from "@angular/material/icon";
import {Subject, takeUntil} from "rxjs";
import {AssistantService} from "../../service/assistant.service";
import {decimalReviver} from "../../utils/decimal-utils";
import {PropertyDetailsComponent} from "../property-details/property-details.component";
import {CommonModule} from "@angular/common";

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [
    MatIcon,
    CommonModule,
    PropertyDetailsComponent
  ],
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss'
})
export class HeaderComponent implements OnInit, OnDestroy{

  unsubscribe: Subject<void> = new Subject();
  protected toolResults: any;
  protected showPropertyDetails: boolean = false;
  constructor(private assistantService: AssistantService) {}

  ngOnDestroy(): void {
    this.unsubscribe.next();
    this.unsubscribe.complete();
  }



  async ngOnInit() {

    this.assistantService.toolProgressSubject
      .pipe(takeUntil(this.unsubscribe))
      .subscribe(completedTool => {

        if(completedTool === "company_overview"){
          this.showPropertyDetails = true;
        }
      })

    this.assistantService.toolResultsSubject
      .pipe(takeUntil(this.unsubscribe))
      .subscribe(json => {
        const modifiedString = json
          .replace(/'/g, '"')
          .replace(/Decimal\("?(-?\d+(?:\.\d+)?)"?\)/g, '$1')
          .replace(/"(-?\d+(?:\.\d+)?)"/g, '$1');
        this.toolResults = JSON.parse(modifiedString, decimalReviver)

      })
  }

}
