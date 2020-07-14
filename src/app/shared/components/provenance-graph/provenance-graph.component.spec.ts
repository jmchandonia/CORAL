import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ProvenanceGraphComponent } from './provenance-graph.component';

describe('ProvenanceGraphComponent', () => {
  let component: ProvenanceGraphComponent;
  let fixture: ComponentFixture<ProvenanceGraphComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ProvenanceGraphComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ProvenanceGraphComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
