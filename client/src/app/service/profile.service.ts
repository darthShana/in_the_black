import {Injectable, OnDestroy, OnInit} from '@angular/core';
import {AssistantService} from "./assistant.service";
import {Subject, takeUntil} from "rxjs";
import {decimalReviver} from "../utils/decimal-utils";

@Injectable({
  providedIn: 'root',
})
export class ProfileService implements OnDestroy{

  unsubscribe: Subject<void> = new Subject();
  metadata: any;
  property_details: any;

  constructor(private assistantService: AssistantService){
    this.assistantService.toolResultsSubject
      .pipe(takeUntil(this.unsubscribe))
      .subscribe(event => {
        let tool = event.name
        if (tool === "company_overview" || tool === "user_greeting"){
          let toolResult = JSON.parse(event.content, decimalReviver);
          console.log('----------profile service------------')
          console.log(toolResult)
          this.metadata = toolResult['metadata']
          this.property_details = toolResult['property_details']
        }

      })
  }

  ngOnDestroy(): void {
    this.unsubscribe.next();
    this.unsubscribe.complete();
  }


}
