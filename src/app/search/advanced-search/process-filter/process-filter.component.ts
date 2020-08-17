import { Component, OnInit, Output, EventEmitter, Input } from '@angular/core';
import { QueryParam } from 'src/app/shared/models/QueryBuilder';
import { Term } from 'src/app/shared/models/brick';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { BsDatepickerConfig } from 'ngx-bootstrap/datepicker';

@Component({
  selector: 'app-process-filter',
  templateUrl: './process-filter.component.html',
  styleUrls: ['./process-filter.component.css'],
})
export class ProcessFilterComponent implements OnInit {

  @Input() queryParams: QueryParam[];

  @Output() removed: EventEmitter<any> = new EventEmitter();

  datePickerConfig: Partial<BsDatepickerConfig> = { containerClass: 'theme-dark-blue' };

  processes: Observable<Term[]>;
  campaigns: Observable<Term[]>;
  personnel: Observable<Term[]>;

  constructor(
    private queryBuilder: QueryBuilderService
  ) { }

  ngOnInit(): void {
    this.processes = this.queryBuilder.getProcessOterms().pipe(map((data: any) => data.results));
    this.campaigns = this.queryBuilder.getCampaignOterms().pipe(map((data: any) => data.results));
    this.personnel = this.queryBuilder.getPersonnelOterms().pipe(map((data: any) => data.results));
  }

  addFilter(event, attribute) {
    if (event) {
      if (event.text) {
        this.queryParams.push(new QueryParam(attribute, '=', event.text, 'string'));
      } else {
        // input is a date, convert to yyyy-mm-dd
        const dateFormat = event.toISOString().split('T')[0];
        this.queryParams.push(new QueryParam(attribute, '=', dateFormat, 'string'));
      }
    } else {
      const idxToRemove = this.queryParams.indexOf(this.queryParams.find(x => x.attribute === attribute));
      this.queryParams.splice(idxToRemove, 1);
    }
  }
}
