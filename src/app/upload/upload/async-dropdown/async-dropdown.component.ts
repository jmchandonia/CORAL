import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { Select2OptionData } from 'ng2-select2';
import { Term } from 'src/app/shared/models/brick';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-async-dropdown',
  templateUrl: './async-dropdown.component.html',
  styleUrls: ['./async-dropdown.component.css']
})
export class AsyncDropdownComponent implements OnInit {

  // @Input() disabled: boolean;
  // @Input() term: Term;
  @Input() set term(selectedValue: Term) {
    if (selectedValue) {
      this.data = [selectedValue];
      this.selectedId = selectedValue.id;
    }
  }
  @Input() required: boolean;
  // @Input() value: string;
  // @Input() callSearchMethod: (term: string) => Observable<any>;
  @Input() method: string;

  @Output() valueChanged: EventEmitter<string> = new EventEmitter();

  data: Array<Select2OptionData> = [];
  selectedId: string;

  options: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
    query: (options: Select2QueryOptions) => {
      const searchTerm = options.term;
      if (searchTerm && searchTerm.length > 3) {
        options.callback({results: []});
      } else {
        // this.callSearchMethod(searchTerm)
        this.uploadService[this.method](searchTerm)
          .subscribe((data: any) => {
            // this.data = data.results;
            options.callback({results: data.results as Select2OptionData});
          });
      }
    }
  };

  constructor(private uploadService: UploadService) {
  }

  ngOnInit() {
  }

  handleValueChange(event) {
    this.valueChanged.emit(event);
  }


}
