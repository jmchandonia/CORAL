import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { OntologyBrowserComponent } from './ontology-browser.component';

describe('OntologyBrowserComponent', () => {
  let component: OntologyBrowserComponent;
  let fixture: ComponentFixture<OntologyBrowserComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ OntologyBrowserComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(OntologyBrowserComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
