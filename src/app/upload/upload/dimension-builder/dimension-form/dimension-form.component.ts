import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { BrickDimension, DimensionVariable } from 'src/app/shared/models/brick';
import { Select2OptionData } from 'ng2-select2';
import { UploadService } from 'src/app/shared/services/upload.service';
@Component({
  selector: 'app-dimension-form',
  templateUrl: './dimension-form.component.html',
  styleUrls: ['./dimension-form.component.css']
})
export class DimensionFormComponent implements OnInit {

  private _dimension: BrickDimension;

  select2Options: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
    query: (options: Select2QueryOptions) => {
      const term = options.term;
      if (!term || term.length < 3) {
        options.callback({results: []});
      } else {
        this.uploadService.searchOntTerms(term)
          .subscribe((data: any) => {
            options.callback({results: data.results as Select2OptionData});
          });
      }
    }
  };

  @Input() set dimension(d: BrickDimension) {
    this._dimension = d;
  }

  get dimension() {
    return this._dimension;
  }

  @Output() deleted = new EventEmitter();
  constructor(private uploadService: UploadService) { }

  ngOnInit() {
  }

  addDimensionVariable() {
    this.dimension.variables.push(
      new DimensionVariable(this.dimension, this.dimension.variables.length)
      );
  }

  removeDimensionVariable(dimVar) {
    this.dimension.variables = this.dimension.variables.filter(item => item !== dimVar);
    this.dimension.resetDimVarIndices();
  }

  delete() {
    this.deleted.emit(this.dimension);
  }

}
