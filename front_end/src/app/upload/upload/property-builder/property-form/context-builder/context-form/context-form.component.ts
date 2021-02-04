import { Component, OnInit, Input, Output, EventEmitter, OnDestroy } from '@angular/core';
import { Context, Term } from 'src/app/shared/models/brick';
import { UploadService } from 'src/app/shared/services/upload.service';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-context-form',
  templateUrl: './context-form.component.html',
  styleUrls: ['./context-form.component.css']
})
export class ContextFormComponent implements OnInit, OnDestroy {


  private _context: Context;

  @Input() set context(c: Context) {
    this._context = c;

    this.typesData = c.typeTerm ? [c.typeTerm] : [];
    this.unitsData = c.units ? [c.units] : [];
    this.valuesData = c.value && c.requireDropdownForVal
      ? [c.value] : [];

    if (c.typeTerm) {
      this.typeItem = c.typeTerm.id;
    }
    if (c.units) {
      this.unitsItem = c.units.id;
    }
    if (c.value && c.requireDropdownForVal) {
      this.valueItem = (c.value as Term).id;
    }

    if (this.context.microType) {
      this.getUnits();
    } else {
      if (this.context.typeTerm) {
        // this code should be removed in the future as template context microtypes shoud ideally be provided in the JSON file
        // it is here to prevent fields from not being able to load units
        this.uploadService.searchPropertyMicroTypes(this.context.typeTerm.text)
          .subscribe((data: any) => {

            // get results from API call and find microtype from there
            const typeData = data.results.find(item => item.id === this.context.typeTerm.id);

            // if we still cant find the microtype after the API call, set the units to null
            if (!typeData) {
              this.context.units = null as Term;
            } else {
              this.context.microType = typeData.microtype;
              this.getUnits();
            }
          });
      }
    }
  }

  get context() { return this._context; }

  @Output() resetContext: EventEmitter<Context> = new EventEmitter();
  @Output() deleted: EventEmitter<any> = new EventEmitter();
  @Output() valueError: EventEmitter<any> = new EventEmitter();
  errorSub: Subscription;

  public typesData: Array<Term>;
  public unitsData: Array<Term>;
  public valuesData: Array<Term>;


  typesLoading = false;
  valuesLoading = false;
  unitsLoading = false;

  typeItem: string;
  unitsItem: string;
  valueItem: string;
  error = false;
  scalarError = false;

  constructor(
    private uploadService: UploadService,
    private validator: UploadValidationService
  ) { }

  ngOnInit() {
    this.errorSub = this.validator.getContextValidationErrors()
      .subscribe(error => this.error = error);
  }

  ngOnDestroy() {
    if (this.errorSub) {
      this.errorSub.unsubscribe();
    }
  }

  handleTypesSearch(event) {
    if (event.term.length) {
      this.typesLoading = true;
      this.uploadService.searchPropertyMicroTypes(event.term).subscribe((data: any) => {
        this.typesData = [...data.results];
        this.typesLoading = false;
      });
    }
  }

  formatOptionLabel(item) {
    // format for displaying microtype dropdown options
    return `${item.definition !== `${item.text}.` ? ` - ${item.definition}` : ''} (${item.scalar_type})`;
  }

  handleValuesSearch(event) {
    if (event.term.length) {
      this.valuesLoading = true;
      if (this.context.scalarType === 'oterm_ref') {
        this.uploadService.searchOntPropertyValues(event.term, this.context.microType)
          .subscribe((data: any) => {
            this.valuesData = [...data.results];
            this.valuesLoading = false;
        });
      } else {
        // scalar type should be object_ref, search for object_refs
        this.uploadService.searchPropertyValueObjectRefs(event.term, this.context.type.id, this.context.microType)
          .subscribe((data: any) => {
            this.valuesData = [...data.results];
            this.valuesLoading = false;
        });
      }
    }
  }

  getUnits() {
    this.unitsLoading = true;
    this.uploadService.searchOntPropertyUnits(this.context.microType)
    .subscribe(data => {
      if (!data.results.length) {
        this.context.units = null as Term;
      } else {
        if (this.context.units === null) {
          this.context.units = undefined;
        }
        this.unitsData = [...data.results];
      }
      this.unitsLoading = false;
  });
  }

  setContextType(event: Term) {
    this.context.typeTerm = event;

    // clear reset entire property object to clear other select 2 dropdowns
    if (this.context.value || this.context.units) {
      const resetProperty = new Context(
        this.context.required,
        event
      );
      // emit new typed property to replace old one in parent component array reference
      this.resetContext.emit(resetProperty);
    } else {
      this.getUnits();
    }
  }

  setValue(event: Term) {
    this.context.value = event;
  }

  setUnits(event: Term) {
    this.context.units = event;
  }

  validateValue() {
    if (!this.validator.validScalarType(this.context.scalarType, this.context.value)) {
      this.scalarError = true;
      this.context.invalidValue = true;
      this.valueError.emit(this.validator.INVALID_VALUE);
    } else {
      this.scalarError = false;
      this.context.invalidValue = false;
      this.valueError.emit(null);
    }
  }

  onDelete() {
    this.deleted.emit();
  }

}
